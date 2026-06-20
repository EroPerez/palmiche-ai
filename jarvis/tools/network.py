import platform
import socket
import subprocess
from typing import Optional


def get_network_info() -> str:
    """Obtiene IP local, SSID de WiFi activo y estado de conexión."""
    lines = []

    # IP local
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            lines.append(f"IP local: {s.getsockname()[0]}")
    except OSError:
        lines.append("IP local: no disponible")

    # IP pública (requiere conexión)
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "3", "https://ifconfig.me"],
            capture_output=True, text=True, timeout=5,
        )
        if r.stdout.strip():
            lines.append(f"IP pública: {r.stdout.strip()}")
    except Exception:
        pass

    sys = platform.system()
    if sys == "Linux":
        # SSID y señal WiFi
        try:
            r = subprocess.run(
                ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "dev", "wifi"],
                capture_output=True, text=True, timeout=5,
            )
            for line in r.stdout.splitlines():
                parts = line.split(":")
                if parts and parts[0] == "yes" and len(parts) >= 4:
                    lines.append(f"WiFi: {parts[1]} | Señal: {parts[2]}% | Seguridad: {parts[3]}")
                    break
        except Exception:
            pass

        # Interfaces de red
        try:
            r = subprocess.run(["ip", "-br", "addr"], capture_output=True, text=True)
            ifaces = [l for l in r.stdout.splitlines() if "UP" in l]
            if ifaces:
                lines.append(f"Interfaces activas: {', '.join(l.split()[0] for l in ifaces)}")
        except Exception:
            pass

    elif sys == "Darwin":
        try:
            r = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                capture_output=True, text=True,
            )
            for line in r.stdout.splitlines():
                if " SSID:" in line:
                    lines.append(f"WiFi: {line.split('SSID:')[1].strip()}")
                    break
        except Exception:
            pass

    return "\n".join(lines) if lines else "No se pudo obtener información de red"


def ping_host(host: str, count: int = 4) -> str:
    """Hace ping a un host y devuelve latencia y pérdida de paquetes.

    Args:
        host: Hostname o IP a hacer ping.
        count: Número de paquetes a enviar. Default: 4.
    """
    count = max(1, min(10, count))
    sys = platform.system()
    flag = "-n" if sys == "Windows" else "-c"
    try:
        r = subprocess.run(
            ["ping", flag, str(count), host],
            capture_output=True, text=True, timeout=count * 3 + 5,
        )
        output = r.stdout.strip() or r.stderr.strip()
        lines = output.splitlines()
        summary = [l for l in lines if "packet" in l.lower() or "ms" in l.lower() or "estadística" in l.lower()]
        return "\n".join(summary) if summary else output[-500:] if len(output) > 500 else output
    except subprocess.TimeoutExpired:
        return f"Ping a {host} tardó demasiado"
    except FileNotFoundError:
        return "Comando 'ping' no encontrado"
    except Exception as e:
        return f"Error al hacer ping a {host}: {e}"
