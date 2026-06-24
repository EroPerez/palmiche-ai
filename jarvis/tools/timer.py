"""Countdown timers and time-based alarms for Jarvis.

Timers run in daemon threads and fire desktop notifications when they expire.
All state is in-memory; timers are lost if the process restarts.
"""
import platform
import subprocess
import threading
import time
import uuid
from datetime import datetime, timedelta

_timers: dict = {}
_lock = threading.Lock()


def _notify(title: str, message: str) -> None:
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.run(["notify-send", "-u", "critical", title, message], check=False)
        elif system == "Darwin":
            script = (
                "on run argv\n"
                "display notification (item 2 of argv) with title (item 1 of argv)\n"
                "end run"
            )
            subprocess.run(["osascript", "-e", script, title, message], check=False)
    except FileNotFoundError:
        pass


def _fire(timer_id: str, label: str) -> None:
    with _lock:
        _timers.pop(timer_id, None)
    _notify("⏰ Temporizador", label or "El temporizador ha finalizado")


def set_timer(seconds: int, label: str = "") -> str:
    """Start a countdown timer for *seconds* seconds. Sends a desktop notification when done."""
    try:
        secs = int(seconds)
    except (TypeError, ValueError):
        return f"Duración inválida: '{seconds}'."
    if secs <= 0:
        return "La duración debe ser mayor que 0 segundos."
    if secs > 86400:
        return "La duración máxima es 24 horas (86400 segundos)."

    tid = uuid.uuid4().hex[:6]
    end_time = time.time() + secs
    t = threading.Timer(secs, _fire, args=(tid, label or "Tiempo completado"))
    t.daemon = True

    with _lock:
        _timers[tid] = {"timer": t, "label": label or "", "end_time": end_time}
    t.start()

    mins, remainder = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        duration_str = f"{hours}h {mins:02d}m {remainder:02d}s"
    elif mins:
        duration_str = f"{mins}m {remainder:02d}s"
    else:
        duration_str = f"{secs}s"

    return (
        f"Temporizador iniciado [{tid}]\n"
        f"Duración: {duration_str}\n"
        f"Etiqueta: {label or '(sin etiqueta)'}"
    )


def set_alarm(alarm_time: str, label: str = "") -> str:
    """Set an alarm for a specific time today (HH:MM, 24h format). If the time has passed, sets for tomorrow."""
    try:
        parsed = datetime.strptime(alarm_time.strip(), "%H:%M")
    except ValueError:
        return f"Hora inválida: '{alarm_time}'. Usa formato HH:MM (24h), ej: 08:30"

    now = datetime.now()
    alarm_dt = now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
    if alarm_dt <= now:
        alarm_dt += timedelta(days=1)

    secs = int((alarm_dt - now).total_seconds())
    day_str = "hoy" if alarm_dt.date() == now.date() else "mañana"
    result = set_timer(secs, label or f"Alarma {alarm_time}")
    return result + f"\nDisparará {day_str} a las {alarm_time}"


def list_timers() -> str:
    """List all active timers with their remaining time."""
    with _lock:
        snapshot = dict(_timers)

    if not snapshot:
        return "No hay temporizadores activos."

    now = time.time()
    lines = [f"{len(snapshot)} temporizador(es) activo(s):"]
    for tid, info in snapshot.items():
        remaining = max(0, info["end_time"] - now)
        mins, secs = divmod(int(remaining), 60)
        hours, mins = divmod(mins, 60)
        if hours:
            time_str = f"{hours}h {mins:02d}m {secs:02d}s"
        elif mins:
            time_str = f"{mins}m {secs:02d}s"
        else:
            time_str = f"{secs}s"
        label = info["label"] or "(sin etiqueta)"
        lines.append(f"  [{tid}] {label} — {time_str} restantes")

    return "\n".join(lines)


def cancel_timer(timer_id: str) -> str:
    """Cancel an active timer by its id."""
    tid = (timer_id or "").strip()
    if not tid:
        return "Indica el id del temporizador a cancelar."

    with _lock:
        info = _timers.pop(tid, None)

    if info is None:
        return f"No se encontró ningún temporizador con id '{tid}'."

    info["timer"].cancel()
    return f"Temporizador [{tid}] '{info['label'] or 'sin etiqueta'}' cancelado."
