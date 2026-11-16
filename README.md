# ollama_telegram_gateway

A Telegram gateway to your local LLM. The model decides whether a tool is needed,
executes it on your PC, and replies — everything stays on your machine.

*User Input → Ollama (decides if a tool is needed) → Execute Tool → Reply.*

## Features

- **Two LLM backends:** Ollama or LM Studio (OpenAI-compatible), switchable via `.env`
- **Tool calling:** the model picks from the tools in `tools/` — each tool is a
  self-contained Python module (`TOOL_NAME`, `TOOL_DESCRIPTION`, `TOOL_PARAMETERS`, `run()`)
- **Conversation history** per user (in-memory, capped via `MAX_HISTORY`)
- **Access control** via Telegram user IDs
- **Optional confirmation gates** before every tool execution (✅/❌ buttons in chat)

## Requirements

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai) running locally
- A model that supports function calling (e.g. `qwen2.5:7b`)

## Setup

**1. Get a Telegram token:**
Message [@BotFather](https://t.me/BotFather) on Telegram and enter `/newbot`. You will receive a token that looks like `123456:ABC-DEF...`.

**2. Create the `.env` file:**

```powershell
Copy-Item .env.example .env
```

Then open the `.env` file and insert your token:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

**3. Make sure Ollama is running:**

```bash
ollama serve             # if not already running
ollama pull qwen2.5:7b   # or your preferred model (must support function calling)
```

**4. Install dependencies & start:**

```powershell
pip install -r requirements.txt
python main.py
```

**Done!** Send `/start` to your bot on Telegram, and it will list all loaded tools.

## Configuration

All settings live in `.env` (see `.env.example`):

| Variable | Description | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather (**required**) | — |
| `ALLOWED_USERS` | Comma-separated Telegram user IDs; empty = everyone | *(empty)* |
| `LLM_BACKEND` | `ollama` or `lmstudio` | `ollama` |
| `OLLAMA_HOST` | Ollama API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model tag (must support function calling) | `qwen2.5:7b` |
| `LMSTUDIO_HOST` | LM Studio API endpoint | `http://localhost:1234` |
| `LMSTUDIO_MODEL` | Model name | `local-model` |
| `TOOL_TIMEOUT` | Tool execution timeout (seconds) | `30` |
| `TOOL_CONFIRMATION` | Require ✅/❌ approval per tool call | `false` |
| `RUN_COMMAND_ALLOWLIST` | Extra commands for the `run_command` tool | *(see below)* |
| `MAX_HISTORY` | Max messages kept per conversation | `50` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

## Commands

| Command | Effect |
|---|---|
| `/start` | Greeting + list of loaded tools (clears history) |
| `/tools` | Detailed list of all tools with descriptions |
| `/clear`, `/reset` | Clear the conversation history |

## Security

- **Restrict access** — with an empty `ALLOWED_USERS` the bot answers every
  Telegram user (a warning is logged at startup). To lock it down:

  ```env
  ALLOWED_USERS=123456789,987654321
  ```

- **Require tool confirmation** — with `TOOL_CONFIRMATION=true`, every tool call
  must first be approved in chat via ✅/❌ buttons before it runs:

  ```env
  TOOL_CONFIRMATION=true
  ```

- **Tool safety: `run_command`** — the `run_command` tool only executes
  whitelisted, read-only PowerShell commands (`ipconfig`, `tasklist`, `dir`, …).
  Command chaining (`;`, `|`, `&`, `>`) is blocked. Extend the whitelist via `.env`:

  ```env
  RUN_COMMAND_ALLOWLIST=get-service,whoami
  ```

- **Secrets hygiene** — `.env` is gitignored; never commit your bot token.

## Project structure

```
main.py                # entry point: loads tools, registers handlers, runs polling
config.py              # .env loading, validation, logging setup
bot/
├── handlers.py        # Telegram handlers, tool loop with confirmation gates
└── conversation.py    # per-user in-memory history
llm/
├── ollama_client.py   # Ollama /api/chat client (dict tool arguments)
└── lmstudio_client.py # LM Studio /v1/chat/completions (JSON tool arguments)
tools/
├── manager.py         # tool discovery, definition export, async execution
├── run_command.py     # whitelisted PowerShell execution
├── crypto_price.py    # CoinGecko prices
├── pc_temp.py         # CPU/GPU temperatures (psutil)
└── system_info.py     # OS, CPU, RAM, disk, network
```

## License

MIT
