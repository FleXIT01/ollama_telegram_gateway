TOOL_NAME = "run_command"
TOOL_DESCRIPTION = "Execute a Windows PowerShell command and return the output. Use when the user asks you to run a terminal command or check system status via command line."

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

SAFE_COMMANDS = []


def run(command: str) -> str:
    import subprocess
    import os

    command = command.strip()
    if not command:
        return "No command provided."

    if SAFE_COMMANDS:
        allowed = any(command.lower().startswith(c.lower()) for c in SAFE_COMMANDS)
        if not allowed:
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
