"""Local calendar / event management for Jarvis.

Events are stored as JSON in EVENTS_FILE (default ~/.jarvis_events.json), so the
calendar works offline and without external accounts. Each event has a short id,
a title, an ISO date (YYYY-MM-DD), an optional time (HH:MM), and optional
description and location fields.
"""
import json
import logging
import uuid
from datetime import date, datetime, timedelta

from ..config import EVENTS_FILE

logger = logging.getLogger(__name__)


def _load() -> list:
    """Read and validate the events file, returning [] on any error."""
    try:
        if EVENTS_FILE.exists():
            raw = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return [e for e in raw if isinstance(e, dict) and e.get("id") and e.get("date")]
    except Exception as exc:  # noqa: BLE001 - corrupt file should not crash the tool
        logger.warning("No se pudo leer %s: %s", EVENTS_FILE, exc)
    return []


def _save(events: list) -> None:
    """Persist *events* to EVENTS_FILE as JSON."""
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    EVENTS_FILE.write_text(
        json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD date, accepting the aliases 'hoy'/'today' and 'mañana'/'tomorrow'."""
    v = (value or "").strip().lower()
    if v in ("hoy", "today"):
        return date.today()
    if v in ("mañana", "manana", "tomorrow"):
        return date.today() + timedelta(days=1)
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def _fmt(event: dict) -> str:
    """Format a single event as a one-line summary."""
    when = event["date"]
    if event.get("time"):
        when += f" {event['time']}"
    line = f"[{event['id']}] {when} — {event.get('title', '(sin título)')}"
    if event.get("location"):
        line += f" @ {event['location']}"
    if event.get("description"):
        line += f"\n      {event['description']}"
    return line


def add_event(
    title: str,
    date: str,
    time: str = "",
    description: str = "",
    location: str = "",
) -> str:
    """Create a calendar event. *date* is YYYY-MM-DD (or 'hoy'/'mañana'); *time* is HH:MM."""
    if not title or not title.strip():
        return "El título del evento no puede estar vacío."
    try:
        iso_date = _parse_date(date).isoformat()
    except (ValueError, TypeError):
        return f"Fecha inválida: '{date}'. Usa el formato YYYY-MM-DD (o 'hoy'/'mañana')."

    clean_time = ""
    if time and time.strip():
        try:
            clean_time = datetime.strptime(time.strip(), "%H:%M").strftime("%H:%M")
        except ValueError:
            return f"Hora inválida: '{time}'. Usa el formato HH:MM (24h)."

    event = {
        "id": uuid.uuid4().hex[:8],
        "title": title.strip(),
        "date": iso_date,
        "time": clean_time,
        "description": description.strip(),
        "location": location.strip(),
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    events = _load()
    events.append(event)
    _save(events)
    return f"Evento creado:\n{_fmt(event)}"


def list_events(start: str = "", end: str = "") -> str:
    """List events sorted by date/time. Optional *start* and *end* (YYYY-MM-DD) filter the range."""
    events = _load()
    if not events:
        return "No hay eventos guardados."

    try:
        start_d = _parse_date(start) if start and start.strip() else None
        end_d = _parse_date(end) if end and end.strip() else None
    except (ValueError, TypeError):
        return "Rango inválido. Usa fechas YYYY-MM-DD (o 'hoy'/'mañana')."

    def in_range(ev: dict) -> bool:
        d = datetime.strptime(ev["date"], "%Y-%m-%d").date()
        if start_d and d < start_d:
            return False
        if end_d and d > end_d:
            return False
        return True

    selected = [e for e in events if in_range(e)]
    if not selected:
        return "No hay eventos en ese rango."

    selected.sort(key=lambda e: (e["date"], e.get("time") or "99:99"))
    header = f"{len(selected)} evento(s):"
    return header + "\n" + "\n".join(_fmt(e) for e in selected)


def upcoming_events(days: int = 7) -> str:
    """List events from today through the next *days* days (default 7)."""
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 7
    days = max(1, min(365, days))
    today = date.today()
    end = today + timedelta(days=days)
    return list_events(today.isoformat(), end.isoformat())


def delete_event(event_id: str) -> str:
    """Delete the event with the given id (the short id shown in brackets)."""
    target = (event_id or "").strip()
    if not target:
        return "Indica el id del evento a eliminar."
    events = _load()
    remaining = [e for e in events if e.get("id") != target]
    if len(remaining) == len(events):
        return f"No se encontró ningún evento con id '{target}'."
    _save(remaining)
    return f"Evento '{target}' eliminado."


if not EVENTS_FILE.exists():
    _save([])
