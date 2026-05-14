from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN, LLM_BACKEND, OLLAMA_HOST, LMSTUDIO_HOST, logger
from bot.handlers import start, handle_message, list_tools, handle_non_text
from tools.manager import discover_tools
import os

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "tools")


def main():
    logger.info(f"Starting Telegram AI Gateway | Backend: {LLM_BACKEND}")

    discover_tools(TOOLS_DIR)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", handle_message))
    app.add_handler(CommandHandler("tools", list_tools))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_non_text))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
