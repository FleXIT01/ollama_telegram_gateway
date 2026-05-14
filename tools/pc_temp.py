TOOL_NAME = "pc_temp"
TOOL_DESCRIPTION = "Get PC temperature readings (CPU, GPU, motherboard). Requires psutil or OpenHardwareMonitor. Use when the user asks about PC temperature or if the computer is running hot."

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


async def run(component: str = "all") -> str:
    try:
        import psutil
    except ImportError:
        return (
            "psutil is not installed. Run: pip install psutil\n"
            "Note: psutil temperature sensors may not work on all Windows systems. "
            "For better GPU temperature support on Windows, consider using OpenHardwareMonitor or GPU-Z."
        )

    temps = psutil.sensors_temperatures()
    if not temps:
        return "No temperature sensors found. This is common on Windows. Try installing OpenHardwareMonitor."

    lines = []
    for name, entries in temps.items():
        for entry in entries:
            label = entry.label or name
            if component == "cpu" and "cpu" not in name.lower():
                continue
            if component == "gpu" and "gpu" not in name.lower():
                continue
            high = entry.high
            critical = entry.critical
            temp_str = f"{label}: {entry.current:.0f}°C"
            if high:
                temp_str += f" (max safe: {high:.0f}°C)"
            if critical:
                temp_str += f" [critical: {critical:.0f}°C]"
            lines.append(temp_str)

    return "\n".join(lines) if lines else "No temperature data found for the specified component."
