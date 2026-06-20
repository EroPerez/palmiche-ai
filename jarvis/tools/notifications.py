import platform
import subprocess


def send_notification(title: str, message: str, urgency: str = "normal") -> str:
    """Send a desktop notification via notify-send (Linux) or osascript (macOS)."""
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.run(
                ["notify-send", "-u", urgency, title, message], check=True
            )
        elif system == "Darwin":
            script = (
                "on run argv\n"
                "set notifTitle to item 1 of argv\n"
                "set notifMessage to item 2 of argv\n"
                "display notification notifMessage with title notifTitle\n"
                "end run"
            )
            subprocess.run(["osascript", "-e", script, title, message], check=True)
        return f"Notificación enviada: '{title}'"
    except FileNotFoundError:
        return "notify-send no encontrado. Instala: sudo apt install libnotify-bin"
    except subprocess.CalledProcessError as e:
        return f"Error al enviar notificación: {e}"
