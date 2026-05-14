from __future__ import annotations

import importlib.util
import inspect
import os
import sys
import asyncio
from config import TOOL_TIMEOUT, logger


class ToolError(Exception):
    pass


class Tool:
    __slots__ = ("name", "description", "parameters", "func", "file_path")

    def __init__(self, name: str, description: str, parameters: dict, func, file_path: str):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func
        self.file_path = file_path


_tools: dict[str, Tool] = {}


def _load_tool_file(filepath: str) -> None:
    filename = os.path.basename(filepath)
    modname = f"tool_{filename[:-3].replace('.', '_')}"

    spec = importlib.util.spec_from_file_location(modname, filepath)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)

    name = getattr(module, "TOOL_NAME", None)
    description = getattr(module, "TOOL_DESCRIPTION", None)
    parameters = getattr(module, "TOOL_PARAMETERS", None)
    run_func = getattr(module, "run", None)

    if not all([name, description, parameters, run_func]):
        logger.warning(f"Skipping {filepath}: missing required attributes (TOOL_NAME, TOOL_DESCRIPTION, TOOL_PARAMETERS, run)")
        return

    _tools[name] = Tool(
        name=str(name),
        description=str(description),
        parameters=parameters,
        func=run_func,
        file_path=filepath,
    )
    logger.info(f"Loaded tool: {name} ({filepath})")


def discover_tools(tools_dir: str) -> None:
    """Scan a directory recursively for tool modules and register them."""
    global _tools
    _tools.clear()

    if not os.path.isdir(tools_dir):
        logger.warning(f"Tools directory not found: {tools_dir}")
        return

    for root, dirs, files in os.walk(tools_dir):
        dirs[:] = [d for d in dirs if not d.startswith("_") and d != "__pycache__"]
        for filename in sorted(files):
            if not filename.endswith(".py") or filename.startswith("_") or filename == "manager.py":
                continue
            filepath = os.path.join(root, filename)
            try:
                _load_tool_file(filepath)
            except Exception as e:
                logger.error(f"Failed to load tool {filepath}: {e}")


def get_tool_definitions() -> list[dict]:
    """Return Ollama-compatible tool function definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in _tools.values()
    ]


async def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with given arguments. Returns the result string."""
    tool = _tools.get(name)
    if not tool:
        raise ToolError(f"Unknown tool: {name}")

    try:
        if inspect.iscoroutinefunction(tool.func):
            result = await asyncio.wait_for(
                tool.func(**arguments), timeout=float(TOOL_TIMEOUT)
            )
        else:
            result = await asyncio.wait_for(
                asyncio.to_thread(tool.func, **arguments),
                timeout=float(TOOL_TIMEOUT),
            )
    except asyncio.TimeoutError:
        raise ToolError(f"Tool '{name}' timed out after {TOOL_TIMEOUT}s")
    except Exception as e:
        raise ToolError(f"Tool '{name}' failed: {e}")

    return str(result)


def get_tool_names() -> list[str]:
    return list(_tools.keys())


def get_tools_info() -> list[tuple[str, str]]:
    """Return list of (name, description) tuples for all loaded tools."""
    return [(t.name, t.description) for t in _tools.values()]
