from __future__ import annotations

import json
import httpx
from config import LMSTUDIO_HOST, LMSTUDIO_MODEL, TOOL_TIMEOUT, logger


async def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
) -> dict:
    """
    Send a chat request to LM Studio (OpenAI-compatible API).
    Returns {"content": str} for text replies or {"tool_calls": [...]} for tool calls.
    """
    payload = {
        "model": model or LMSTUDIO_MODEL,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=float(TOOL_TIMEOUT * 3)) as client:
        resp = await client.post(
            f"{LMSTUDIO_HOST}/v1/chat/completions", json=payload
        )
        resp.raise_for_status()
        data = resp.json()

    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    tool_calls = msg.get("tool_calls")

    if tool_calls:
        parsed = []
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}
            parsed.append({"name": name, "arguments": arguments})
        logger.info(f"LLM requested tool calls: {[t['name'] for t in parsed]}")
        return {"tool_calls": parsed}

    content = msg.get("content", "")
    return {"content": content}
