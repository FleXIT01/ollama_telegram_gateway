from __future__ import annotations

import json
import copy
import httpx
from config import LMSTUDIO_HOST, LMSTUDIO_MODEL, TOOL_TIMEOUT, logger


def _to_openai_messages(messages: list[dict]) -> list[dict]:
    """Convert Ollama-format messages (dict arguments) to OpenAI format (JSON string arguments)."""
    converted = []
    for msg in messages:
        msg = copy.deepcopy(msg)
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                func = tc.setdefault("function", {})
                if isinstance(func.get("arguments"), dict):
                    func["arguments"] = json.dumps(func["arguments"])
                tc["type"] = "function"
        if msg.get("role") == "tool":
            msg.pop("tool_call_id", None)
        converted.append(msg)
    return converted


async def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
) -> dict:
    """Send a chat request to LM Studio (OpenAI-compatible API). Returns {"content": str} or {"tool_calls": [...]}."""
    payload = {
        "model": model or LMSTUDIO_MODEL,
        "messages": _to_openai_messages(messages),
        "stream": False,
    }
    if tools:
        payload["tools"] = tools

    try:
        async with httpx.AsyncClient(timeout=float(TOOL_TIMEOUT * 3)) as client:
            resp = await client.post(
                f"{LMSTUDIO_HOST}/v1/chat/completions", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        raise ConnectionError(f"Cannot connect to LM Studio at {LMSTUDIO_HOST}. Is it running?")
    except httpx.HTTPStatusError as e:
        raise ConnectionError(f"LM Studio error ({e.response.status_code}): {e.response.text[:500]}")
    except httpx.TimeoutException:
        raise ConnectionError(f"LM Studio timed out after {TOOL_TIMEOUT * 3}s")
    except httpx.HTTPError as e:
        raise ConnectionError(f"LM Studio request failed: {e}")

    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    tool_calls = msg.get("tool_calls")

    if tool_calls:
        parsed = []
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            raw_args = func.get("arguments", "{}")
            try:
                arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except (json.JSONDecodeError, TypeError):
                arguments = {}
            parsed.append({"name": name, "arguments": arguments})
        logger.info(f"LLM requested tool calls: {[t['name'] for t in parsed]}")
        return {"tool_calls": parsed}

    content = msg.get("content", "")
    return {"content": content}
