from __future__ import annotations

from collections import defaultdict
from config import MAX_HISTORY, logger

_conversations: dict[int, list[dict]] = defaultdict(list)


def get_history(chat_id: int) -> list[dict]:
    return _conversations[chat_id]


def add_message(chat_id: int, role: str, content: str) -> None:
    _conversations[chat_id].append({"role": role, "content": content})
    if len(_conversations[chat_id]) > MAX_HISTORY:
        _conversations[chat_id] = _conversations[chat_id][-MAX_HISTORY:]


def add_tool_call(chat_id: int, tool_name: str, arguments: dict, result: str) -> None:
    """Add a tool call + result as messages in Ollama format.

    Ollama uses dict arguments (not JSON strings like OpenAI).
    """
    _conversations[chat_id].append({
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "function": {
                "name": tool_name,
                "arguments": arguments,
            },
        }],
    })
    _conversations[chat_id].append({
        "role": "tool",
        "content": result,
    })
    if len(_conversations[chat_id]) > MAX_HISTORY:
        _conversations[chat_id] = _conversations[chat_id][-MAX_HISTORY:]


def clear_history(chat_id: int) -> None:
    _conversations[chat_id].clear()
    logger.info(f"Cleared conversation history for chat {chat_id}")
