from __future__ import annotations

import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ALLOWED_USERS, LLM_BACKEND, TOOL_CONFIRMATION, logger
from bot.conversation import get_history, add_message, add_tool_call, clear_history
from tools.manager import get_tool_definitions, get_tool_names, get_tools_info, execute_tool, ToolError

if LLM_BACKEND == "lmstudio":
    from llm.lmstudio_client import chat as llm_chat
else:
    from llm.ollama_client import chat as llm_chat

SYSTEM_PROMPT = """You are a helpful AI assistant running locally. You have access to tools that can perform actions on the user's computer.

- Use tools when they are relevant to the user's request.
- When a user asks you to do something, check if any of the available tools can help.
- Always report tool results back to the user in a helpful, natural way.
- Keep responses concise and to the point.
- If no tool can help, just answer conversationally using your knowledge.
- You can use multiple tools in sequence if needed."""

MAX_TOOL_ROUNDS = 5

_pending_calls: dict[str, tuple[int, list]] = {}


def _is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _is_allowed(user.id):
        await update.message.reply_text("Access denied.")
        return
    tools = get_tool_names()
    tool_list = "\n".join(f"  / {name}" for name in tools) if tools else "  (no tools loaded)"
    confirm_hint = (
        "\nTool execution requires your confirmation." if TOOL_CONFIRMATION else ""
    )
    await update.message.reply_text(
        f"AI Gateway ready.\nModel: {LLM_BACKEND}\nLoaded tools:\n{tool_list}{confirm_hint}\n\nSend me a message!"
    )
    clear_history(user.id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _is_allowed(user.id):
        await update.message.reply_text("Access denied.")
        return

    user_text = update.message.text.strip()
    chat_id = user.id
    logger.info(f"[{chat_id}] User: {user_text}")

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    if user_text.lower() in ("/clear", "/reset"):
        clear_history(chat_id)
        await update.message.reply_text("Conversation cleared.")
        return

    add_message(chat_id, "user", user_text)
    await _run_turn(update, chat_id)


async def _run_turn(update: Update, chat_id: int) -> None:
    """Ask the LLM for the next step and execute tool calls (with optional confirmation)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(chat_id)
    tools = get_tool_definitions()

    try:
        result = await llm_chat(messages, tools=tools if tools else None)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        await update.message.reply_text(f"Error contacting LLM: {e}")
        return

    for _ in range(MAX_TOOL_ROUNDS):
        if result.get("content"):
            add_message(chat_id, "assistant", result["content"])
            await update.message.reply_text(result["content"])
            return

        tool_calls = result.get("tool_calls") or []
        if not tool_calls:
            await update.message.reply_text("The model returned an empty response. Please try again.")
            return

        if TOOL_CONFIRMATION:
            await _ask_confirmation(update, chat_id, tool_calls)
            return

        await _execute_tool_calls(update, chat_id, tool_calls)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(chat_id)
        try:
            result = await llm_chat(messages, tools=tools if tools else None)
        except Exception as e:
            logger.error(f"LLM error after tool calls: {e}")
            await update.message.reply_text(f"Error after tool execution: {e}")
            return

    await update.message.reply_text("Reached tool call limit. Please try again.")


async def _execute_tool_calls(update: Update, chat_id: int, tool_calls: list) -> None:
    for tc in tool_calls:
        name = tc["name"]
        args = tc["arguments"]
        logger.info(f"[{chat_id}] Executing tool: {name}({args})")
        try:
            tool_result = await execute_tool(name, args)
        except ToolError as e:
            tool_result = f"Error: {e}"
            logger.error(f"[{chat_id}] Tool error: {e}")
        add_tool_call(chat_id, name, args, tool_result)


async def _ask_confirmation(update: Update, chat_id: int, tool_calls: list) -> None:
    call_id = uuid.uuid4().hex[:12]
    _pending_calls[call_id] = (chat_id, tool_calls)
    names = ", ".join(tc["name"] for tc in tool_calls)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Execute", callback_data=f"tool:yes:{call_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"tool:no:{call_id}"),
        ]
    ])
    await update.message.reply_text(f"Execute tool(s): {names}?", reply_markup=keyboard)


async def handle_tool_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "tool":
        return
    action, call_id = parts[1], parts[2]

    user = update.effective_user
    entry = _pending_calls.pop(call_id, None)
    if entry is None:
        await query.edit_message_text("This confirmation has expired. Please send your request again.")
        return
    if not _is_allowed(user.id) or user.id != entry[0]:
        await query.edit_message_text("Not authorized for this confirmation.")
        return

    chat_id, tool_calls = entry
    if action != "yes":
        await query.edit_message_text("Cancelled.")
        return

    await query.edit_message_text(
        f"Executing: {', '.join(tc['name'] for tc in tool_calls)}"
    )
    await _execute_tool_calls(update, chat_id, tool_calls)
    await _run_turn(update, chat_id)


async def list_tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _is_allowed(user.id):
        await update.message.reply_text("Access denied.")
        return
    tools = get_tools_info()
    if not tools:
        await update.message.reply_text("No tools loaded.")
        return
    lines = ["**Available tools:**", ""]
    for name, description in tools:
        lines.append(f"`{name}` — {description}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _is_allowed(user.id):
        return
    await update.message.reply_text("I can only process text messages. What would you like me to do?")
