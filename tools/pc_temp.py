TOOL_NAME = "pc_temp"
TOOL_DESCRIPTION = "Get PC temperature readings (CPU, GPU). Requires psutil. Use when the user asks about PC temperature or if the computer is running hot."

TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "component": {
            "type": "string",
            "enum": ["cpu", "gpu", "all"],
            "description": "Which component to check temperature for"
        }
    },
    "required": []
}


def run(component: str = "all") -> str:
    try:
        import psutil
    except ImportError:
        return "psutil not installed. Run: pip install psutil"

    try:
        temps = psutil.sensors_temperatures()
    except Exception as e:
        return f"Error reading sensors: {e}"

    if not temps:
        return "No temperature sensors found. This is common on desktop Windows — try OpenHardwareMonitor or HWMonitor."

    lines = []
    for name, entries in temps.items():
        for entry in entries:
            label = entry.label or name
            if component != "all":
                comp_lower = component.lower()
                if comp_lower not in name.lower() and comp_lower not in label.lower():
                    continue
            temp_str = f"{label}: {entry.current:.0f}C"
            if entry.high:
                temp_str += f" (warning at {entry.high:.0f}C)"
            if entry.critical:
                temp_str += f" [critical at {entry.critical:.0f}C]"
            lines.append(temp_str)

    return "\n".join(lines) if lines else f"No {component} temperature data found."
