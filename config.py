import os
import logging
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_list(key: str, default: str = "") -> list[int]:
    val = os.getenv(key, default).strip()
    if not val:
        return []
    return [int(x.strip()) for x in val.split(",") if x.strip().isdigit()]


TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and add your token from @BotFather."
    )

ALLOWED_USERS: list[int] = _get_list("ALLOWED_USERS")

LLM_BACKEND: str = os.getenv("LLM_BACKEND", "ollama")

OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

LMSTUDIO_HOST: str = os.getenv("LMSTUDIO_HOST", "http://localhost:1234")
LMSTUDIO_MODEL: str = os.getenv("LMSTUDIO_MODEL", "local-model")

TOOL_TIMEOUT: int = int(os.getenv("TOOL_TIMEOUT", "30"))
TOOL_CONFIRMATION: bool = os.getenv("TOOL_CONFIRMATION", "false").lower() == "true"
MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "50"))

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("telegram_ai_gateway")
