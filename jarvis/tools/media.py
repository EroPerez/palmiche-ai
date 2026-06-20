import platform
import subprocess
from typing import Literal


def media_control(action: Literal["play", "pause", "next", "previous", "stop", "status"]) -> str:
    """Controla la reproducción de medios (música/video).

    Args:
        action: play, pause, next, previous, stop o status.
    """
    sys = platform.system()

    if sys == "Linux":
        # playerctl soporta MPRIS (Spotify, VLC, mpv, Chrome, Firefox...)
        try:
            if action == "status":
                r = subprocess.run(
                    ["playerctl", "status"], capture_output=True, text=True
                )
                title = subprocess.run(
                    ["playerctl", "metadata", "title"], capture_output=True, text=True
                )
                artist = subprocess.run(
                    ["playerctl", "metadata", "artist"], capture_output=True, text=True
                )
                status = r.stdout.strip()
                meta = []
                if title.stdout.strip():
                    meta.append(f"🎵 {title.stdout.strip()}")
                if artist.stdout.strip():
                    meta.append(f"🎤 {artist.stdout.strip()}")
                return f"{status} — {' | '.join(meta)}" if meta else status or "Sin reproductor activo"

            cmd_map = {
                "play": "play",
                "pause": "pause",
                "next": "next",
                "previous": "previous",
                "stop": "stop",
            }
            subprocess.run(["playerctl", cmd_map[action]], check=True)
            labels = {
                "play": "Reproduciendo",
                "pause": "Pausado",
                "next": "Siguiente pista",
                "previous": "Pista anterior",
                "stop": "Detenido",
            }
            return labels[action]
        except FileNotFoundError:
            return "playerctl no encontrado. Instala: sudo apt install playerctl"
        except subprocess.CalledProcessError:
            return "Sin reproductor de medios activo"

    elif sys == "Darwin":
        scripts = {
            "play": 'tell application "Music" to play',
            "pause": 'tell application "Music" to pause',
            "next": 'tell application "Music" to next track',
            "previous": 'tell application "Music" to previous track',
            "stop": 'tell application "Music" to stop',
            "status": 'tell application "Music" to get {player state, name of current track, artist of current track}',
        }
        try:
            r = subprocess.run(
                ["osascript", "-e", scripts[action]], capture_output=True, text=True
            )
            if action == "status":
                return r.stdout.strip() or "Sin reproducción activa"
            labels = {
                "play": "Reproduciendo", "pause": "Pausado",
                "next": "Siguiente pista", "previous": "Pista anterior", "stop": "Detenido",
            }
            return labels[action]
        except Exception as e:
            return f"Error al controlar medios: {e}"

    return f"Control de medios no soportado en {sys}"


def get_media_status() -> str:
    """Obtiene el título, artista y estado actual del reproductor de medios activo."""
    return media_control("status")
