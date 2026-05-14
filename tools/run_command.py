TOOL_NAME = "run_command"
TOOL_DESCRIPTION = "Execute a Windows PowerShell command and return the output. SECURITY NOTE: This tool runs commands on the host machine. Only use it with trusted inputs."

TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The PowerShell command to execute"
        }
    },
    "required": ["command"]
}

# Whitelist: only these command prefixes are allowed. Empty = allow all.
# Add safe commands here, e.g.: "ipconfig", "netstat", "tasklist"
SAFE_COMMANDS = []


async def run(command: str) -> str:
    import subprocess

    command = command.strip()
    if not command:
        return "No command provided."

    if SAFE_COMMANDS:
        allowed = any(command.lower().startswith(c.lower()) for c in SAFE_COMMANDS)
        if not allowed:
            return f"Command blocked by whitelist. Allowed commands: {', '.join(SAFE_COMMANDS)}"

    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            timeout=15,
            shell=False,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output[:2000] if len(output) > 2000 else output
    except subprocess.TimeoutExpired:
        return "Command timed out (15s)."
    except FileNotFoundError:
        return "PowerShell not found on this system."
