# ollama_telegram_gateway

**1. Get a Telegram Token:**
Message [@BotFather](https://t.me/BotFather) on Telegram and enter `/newbot`. Choose a name for your bot. You will receive a token that looks like `123456:ABC-DEF...`.

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

The defaults in the `.env` are set correctly (`OLLAMA_HOST=http://localhost:11434`, `OLLAMA_MODEL=qwen2.5:7b`). If you want to use a different model, simply change the model name in the `.env` file.

**4. Install dependencies & start:**
Navigate to the project folder and run:

```powershell
pip install -r requirements.txt
python main.py

```

**Done!** Send `/start` to your bot on Telegram, and it will list all loaded tools.
The flow for every message is:
*User Input → Ollama (decides if a tool is needed) → Execute Tool → Reply.*

**Optional: Restrict Access**
If you want to allow only specific users to interact with the bot, add this line to your `.env` file:

```env
ALLOWED_USERS=123456789,987654321

```

If `ALLOWED_USERS` is empty, the bot answers every Telegram user (a warning is logged at startup).

**Optional: Require tool confirmation**
With `TOOL_CONFIRMATION=true`, every tool call must first be approved in chat via ✅/❌ buttons
before it runs:

```env
TOOL_CONFIRMATION=true
```

**Tool safety: `run_command`**
The `run_command` tool only executes whitelisted, read-only PowerShell commands
(`ipconfig`, `tasklist`, `dir`, …). Command chaining (`;`, `|`, `&`, `>`) is blocked.
Extend the whitelist via `.env`:

```env
RUN_COMMAND_ALLOWLIST=get-service,whoami
```

