import subprocess
import platform
import time
import psutil

from ..config import JARVIS_SUDO_PASSWORD


def get_system_info() -> str:
    """Return a formatted summary of CPU, RAM, disk usage, and system uptime."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime_secs = time.time() - psutil.boot_time()
    h, m = int(uptime_secs // 3600), int((uptime_secs % 3600) // 60)

    return (
        f"Sistema: {platform.system()} {platform.release()}\n"
        f"CPU: {cpu:.1f}% ({psutil.cpu_count(logical=False)} núcleos físicos, "
        f"{psutil.cpu_count()} lógicos)\n"
        f"RAM: {mem.percent:.1f}% usado "
        f"({mem.used / 1024**3:.1f} GB / {mem.total / 1024**3:.1f} GB)\n"
        f"Disco /: {disk.percent:.1f}% usado "
        f"({disk.used / 1024**3:.1f} GB / {disk.total / 1024**3:.1f} GB)\n"
        f"Uptime: {h}h {m}m"
    )


def get_battery_info() -> str:
    """Return battery percentage, charging status, and estimated time remaining."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "No se detectó batería (posiblemente es un desktop)"

    status = "Cargando" if battery.power_plugged else "Descargando"
    secs = battery.secsleft

    if secs == psutil.POWER_TIME_UNLIMITED:
        time_str = "∞ (conectado a corriente)"
    elif secs == psutil.POWER_TIME_UNKNOWN or secs < 0:
        time_str = "tiempo desconocido"
    else:
        time_str = f"{secs // 3600}h {(secs % 3600) // 60}m restantes"

    return f"Batería: {battery.percent:.0f}% — {status} — {time_str}"


def control_volume(action: str, value: int = None) -> str:
    """Get or change the system volume (get/set/up/down/mute/unmute) on Linux or macOS."""
    system = platform.system()

    if system == "Linux":
        cmds = {
            "get": ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            "mute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"],
            "unmute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
        }
        if action == "get":
            r = subprocess.run(cmds["get"], capture_output=True, text=True)
            return r.stdout.strip() or "No se pudo obtener volumen"
        if action == "set" and value is not None:
            v = max(0, min(150, value))
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{v}%"])
            return f"Volumen → {v}%"
        if action == "up":
            inc = value or 10
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{inc}%"])
            return f"Volumen subido {inc}%"
        if action == "down":
            dec = value or 10
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{dec}%"])
            return f"Volumen bajado {dec}%"
        if action in ("mute", "unmute"):
            subprocess.run(cmds[action])
            return "Audio silenciado" if action == "mute" else "Audio activado"

    elif system == "Darwin":
        if action == "get":
            r = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True, text=True,
            )
            return f"Volumen → {r.stdout.strip()}%" if r.stdout.strip() else "No se pudo obtener volumen"
        if action == "set" and value is not None:
            v = max(0, min(100, value))
            subprocess.run(["osascript", "-e", f"set volume output volume {v}"])
            return f"Volumen → {v}%"
        if action in ("up", "down"):
            step = max(1, min(100, value if value is not None else 10))
            sign = "+" if action == "up" else "-"
            subprocess.run([
                "osascript", "-e",
                f"set volume output volume ((output volume of (get volume settings)) {sign} {step})"
            ])
            label = "subido" if action == "up" else "bajado"
            return f"Volumen {label} {step}%"
        if action == "mute":
            subprocess.run(["osascript", "-e", "set volume output muted true"])
            return "Audio silenciado"
        if action == "unmute":
            subprocess.run(["osascript", "-e", "set volume output muted false"])
            return "Audio activado"

    return f"Acción '{action}' no soportada en {system}"


def control_brightness(action: str, value: int = None) -> str:
    """Get or change screen brightness via brightnessctl (Linux only)."""
    try:
        if action == "get":
            cur = int(subprocess.run(["brightnessctl", "get"], capture_output=True, text=True).stdout.strip())
            mx = int(subprocess.run(["brightnessctl", "max"], capture_output=True, text=True).stdout.strip())
            return f"Brillo actual: {int(cur / mx * 100)}%"
        if action == "set" and value is not None:
            v = max(5, min(100, value))
            subprocess.run(["brightnessctl", "set", f"{v}%"])
            return f"Brillo → {v}%"
        if action == "up":
            inc = value or 10
            subprocess.run(["brightnessctl", "set", f"+{inc}%"])
            return f"Brillo subido {inc}%"
        if action == "down":
            dec = value or 10
            subprocess.run(["brightnessctl", "set", f"{dec}%-"])
            return f"Brillo bajado {dec}%"
    except FileNotFoundError:
        return "brightnessctl no encontrado. Instala: sudo apt install brightnessctl"
    return f"Acción '{action}' ejecutada"


def _run_power_cmd(cmd: list) -> tuple[bool, str]:
    """Run a power/lock command and report whether it succeeded.

    Returns (ok, error). Unlike a fire-and-forget Popen, this waits for the
    command and inspects its exit code so real failures (missing binary,
    polkit/permission denial, no active session) surface instead of being
    silently reported as success. A TimeoutExpired is treated as success
    because actions like suspend may not return promptly.

    If the command starts with ``sudo`` and ``JARVIS_SUDO_PASSWORD`` is set,
    ``-S`` is injected so the password can be piped via stdin.
    """
    actual_cmd = list(cmd)
    stdin_data = None

    if cmd and cmd[0] == "sudo" and JARVIS_SUDO_PASSWORD:
        if "-S" not in actual_cmd:
            actual_cmd.insert(1, "-S")
        stdin_data = JARVIS_SUDO_PASSWORD + "\n"

    try:
        r = subprocess.run(
            actual_cmd, capture_output=True, text=True, timeout=15,
            input=stdin_data,
        )
    except FileNotFoundError:
        return False, f"{cmd[0]}: comando no encontrado"
    except subprocess.TimeoutExpired:
        return True, ""
    if r.returncode == 0:
        return True, ""
    err = (r.stderr or r.stdout or "").strip()
    return False, f"{cmd[0]}: {err or f'código de salida {r.returncode}'}"


def power_action(action: str) -> str:
    """Perform a system power action: shutdown, restart, sleep, or lock."""
    system = platform.system()
    actions_linux = {
        "shutdown": ["systemctl", "poweroff"],
        "restart": ["systemctl", "reboot"],
        "sleep": ["systemctl", "suspend"],
    }
    actions_mac = {
        "shutdown": ["sudo", "shutdown", "-h", "now"],
        "restart": ["sudo", "shutdown", "-r", "now"],
        "sleep": ["pmset", "sleepnow"],
    }

    if action == "lock":
        if system == "Linux":
            errors = []
            for cmd in (
                ["loginctl", "lock-session"],
                ["gnome-screensaver-command", "-l"],
                ["xdg-screensaver", "lock"],
                ["i3lock"],
            ):
                ok, err = _run_power_cmd(cmd)
                if ok:
                    return "Pantalla bloqueada"
                errors.append(err)
            return "No se pudo bloquear la pantalla. Detalles: " + "; ".join(errors)
        if system == "Darwin":
            ok, err = _run_power_cmd(["pmset", "displaysleepnow"])
            return "Pantalla bloqueada" if ok else f"No se pudo bloquear la pantalla. {err}"
        return f"Acción 'lock' no soportada en {system}"

    if system == "Linux":
        cmds = actions_linux
    elif system == "Darwin":
        cmds = actions_mac
    else:
        return f"Acción '{action}' no soportada en {system}"

    if action in cmds:
        labels = {"shutdown": "Apagando", "restart": "Reiniciando", "sleep": "Suspendiendo"}
        ok, err = _run_power_cmd(cmds[action])
        if ok:
            return f"{labels[action]} el sistema..."
        return (
            f"No se pudo ejecutar '{action}'. {err}. "
            "Puede requerir permisos (polkit/sudo) o una sesión activa."
        )

    return f"Acción '{action}' no reconocida"
