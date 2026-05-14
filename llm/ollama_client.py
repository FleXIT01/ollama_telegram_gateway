from __future__ import annotations

import json
import httpx
from config import OLLAMA_HOST, OLLAMA_MODEL, TOOL_TIMEOUT, logger


async def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
) -> dict:
    """Send a chat request to Ollama. Returns {"content": str} or {"tool_calls": [...]}."""
    payload = {
        "model": model or OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools

    try:
        async with httpx.AsyncClient(timeout=float(TOOL_TIMEOUT * 3)) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        raise ConnectionError(f"Cannot connect to Ollama at {OLLAMA_HOST}. Is it running?")
    except httpx.HTTPStatusError as e:
        raise ConnectionError(f"Ollama error ({e.response.status_code}): {e.response.text[:500]}")
    except httpx.TimeoutException:
        raise ConnectionError(f"Ollama timed out after {TOOL_TIMEOUT * 3}s")
    except httpx.HTTPError as e:
        raise ConnectionError(f"Ollama request failed: {e}")

    msg = data.get("message", {})
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
