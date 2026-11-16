import os

TOOL_NAME = "run_command"
TOOL_DESCRIPTION = (
    "Execute a whitelisted, read-only Windows PowerShell command and return the output. "
    "Use when the user asks you to run a terminal command or check system status via command line. "
    "Only the first word of the command is matched against the whitelist and command chaining "
    "(; | & > etc.) is blocked."
)

TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The PowerShell command to execute (e.g. 'ipconfig', 'tasklist', 'dir')"
        }
    },
    "required": ["command"]
}

_DEFAULT_ALLOWLIST = [
    "ipconfig",
    "tasklist",
    "whoami",
    "hostname",
    "systeminfo",
    "ping",
    "nslookup",
    "get-date",
    "get-process",
    "get-childitem",
    "get-volume",
    "get-disk",
    "netstat",
    "dir",
]

_extra = [
    entry.strip().lower()
    for entry in os.getenv("RUN_COMMAND_ALLOWLIST", "").split(",")
    if entry.strip()
]
SAFE_COMMANDS = [entry.lower() for entry in _DEFAULT_ALLOWLIST] + _extra

_BLOCKED_CHARS = (";", "|", "&", "`", "\n", "\r", "$(", "${", ">")


def run(command: str) -> str:
    import subprocess

    command = command.strip()
    if not command:
        return "No command provided."

    lowered = command.lower()
    if any(marker in lowered for marker in _BLOCKED_CHARS):
        return "Blocked: command chaining or redirection (; | & > etc.) is not allowed."

    first_word = lowered.split()[0]
    if SAFE_COMMANDS and first_word not in SAFE_COMMANDS:
        return f"Command blocked by whitelist. Allowed: {', '.join(SAFE_COMMANDS)}"

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = (result.stdout + result.stderr).strip()
        if not output:
            return "Command completed with no output."
        return output[:2000] if len(output) > 2000 else output
    except subprocess.TimeoutExpired:
        return "Command timed out (15s)."
    except FileNotFoundError:
        return "PowerShell not found."
    except Exception as e:
        return f"Command failed: {e}"
