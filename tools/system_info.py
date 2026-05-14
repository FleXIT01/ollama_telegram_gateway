TOOL_NAME = "system_info"
TOOL_DESCRIPTION = "Get system information: OS, CPU, RAM usage, disk usage, uptime. Use when the user asks about their PC status, performance, or specs."

TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "info_type": {
            "type": "string",
            "enum": ["overview", "cpu", "memory", "disk", "network"],
            "description": "What type of system information to retrieve"
        }
    },
    "required": []
}


async def run(info_type: str = "overview") -> str:
    import platform
    import os
    import shutil
    import time

    lines = []

    if info_type in ("overview", "cpu"):
        lines.append(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
        lines.append(f"Architecture: {platform.machine()}")
        lines.append(f"Hostname: {platform.node()}")
        try:
            import psutil
            cpu_pct = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_phys = psutil.cpu_count(logical=False)
            lines.append(f"CPU: {cpu_count} logical cores ({cpu_phys} physical) at {cpu_pct}% usage")
            freq = psutil.cpu_freq()
            if freq:
                lines.append(f"CPU Frequency: {freq.current:.0f} MHz")
        except ImportError:
            lines.append("CPU: install 'psutil' for detailed CPU info")

    if info_type in ("overview", "memory"):
        try:
            import psutil
            mem = psutil.virtual_memory()
            lines.append(f"RAM: {mem.used / (1024**3):.1f} GB / {mem.total / (1024**3):.1f} GB ({mem.percent}%)")
            swap = psutil.swap_memory()
            if swap.total > 0:
                lines.append(f"Swap: {swap.used / (1024**3):.1f} GB / {swap.total / (1024**3):.1f} GB")
        except ImportError:
            lines.append("RAM: install 'psutil' for detailed memory info")

    if info_type in ("overview", "disk"):
        lines.append(f"Current directory: {os.getcwd()}")
        disk = shutil.disk_usage(os.getcwd())
        lines.append(f"Disk: {disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB ({100 * disk.used / disk.total:.0f}%)")
        try:
            import psutil
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    lines.append(f"  {part.mountpoint} ({part.device}): {usage.percent}% used")
                except PermissionError:
                    pass
        except ImportError:
            pass

    if info_type == "network":
        try:
            import psutil
            for name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if str(addr.family).endswith("AF_INET"):
                        lines.append(f"Network: {name} -> {addr.address}")
        except ImportError:
            lines.append("Network: install 'psutil' for network info")

    return "\n".join(lines) if lines else "No information available."
