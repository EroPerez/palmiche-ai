import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


def take_screenshot(path: Optional[str] = None, selection: bool = False) -> str:
    """Toma una captura de pantalla y la guarda en un archivo.

    Args:
        path: Ruta del archivo de destino. Si no se indica, se guarda en ~/Capturas/ con timestamp.
        selection: Si es True, permite seleccionar un área de la pantalla (solo Linux/macOS).
    """
    if path:
        dest = Path(path).expanduser()
    else:
        captures_dir = Path.home() / "Capturas"
        captures_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = captures_dir / f"captura_{ts}.png"

    sys = platform.system()

    try:
        if sys == "Linux":
            # Intentar scrot, gnome-screenshot, import (ImageMagick)
            if selection:
                for cmd in (
                    ["scrot", "-s", str(dest)],
                    ["gnome-screenshot", "-a", "-f", str(dest)],
                ):
                    try:
                        subprocess.run(cmd, check=True, timeout=30)
                        return f"Captura de selección guardada en: {dest}"
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue
                return "No se encontró herramienta de captura por selección. Instala: sudo apt install scrot"
            else:
                for cmd in (
                    ["scrot", str(dest)],
                    ["gnome-screenshot", "-f", str(dest)],
                    ["import", "-window", "root", str(dest)],
                ):
                    try:
                        subprocess.run(cmd, check=True, timeout=10)
                        return f"Captura guardada en: {dest}"
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue
                return "No se encontró herramienta de captura. Instala: sudo apt install scrot"

        elif sys == "Darwin":
            cmd = ["screencapture"]
            if selection:
                cmd.append("-i")
            cmd.append(str(dest))
            subprocess.run(cmd, check=True, timeout=30)
            return f"Captura guardada en: {dest}"

        return f"Captura de pantalla no soportada en {sys}"

    except subprocess.TimeoutExpired:
        return "Captura cancelada (tiempo de espera agotado)"
    except Exception as e:
        return f"Error al tomar captura: {e}"
