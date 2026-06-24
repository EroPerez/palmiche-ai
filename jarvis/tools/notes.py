"""Personal notes manager for Jarvis.

Notes are stored as JSON in NOTES_FILE (default ~/.jarvis_notes.json).
Each note has a short id, title, content, optional tags list, and timestamps.
"""
import json
import logging
import uuid
from datetime import datetime

from ..config import NOTES_FILE

logger = logging.getLogger(__name__)


def _load() -> list:
    try:
        if NOTES_FILE.exists():
            raw = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return [n for n in raw if isinstance(n, dict) and n.get("id") and n.get("title")]
    except Exception as exc:
        logger.warning("No se pudo leer %s: %s", NOTES_FILE, exc)
    return []


def _save(notes: list) -> None:
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")


def _fmt_short(note: dict) -> str:
    tags = f" [{', '.join(note['tags'])}]" if note.get("tags") else ""
    updated = note.get("updated", note.get("created", ""))[:10]
    snippet = note.get("content", "")[:60].replace("\n", " ")
    if len(note.get("content", "")) > 60:
        snippet += "…"
    return f"[{note['id']}] {note['title']}{tags} ({updated})\n    {snippet}"


def create_note(title: str, content: str, tags: str = "") -> str:
    """Create a new note or update an existing one with the same title."""
    if not title or not title.strip():
        return "El título de la nota no puede estar vacío."

    clean_title = title.strip()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    now = datetime.now().isoformat(timespec="seconds")

    notes = _load()
    existing = next((n for n in notes if n["title"].lower() == clean_title.lower()), None)

    if existing:
        existing["content"] = content
        existing["tags"] = tag_list
        existing["updated"] = now
        _save(notes)
        return f"Nota actualizada: '{clean_title}' [{existing['id']}]"

    note = {
        "id": uuid.uuid4().hex[:8],
        "title": clean_title,
        "content": content,
        "tags": tag_list,
        "created": now,
        "updated": now,
    }
    notes.append(note)
    _save(notes)
    return f"Nota creada: '{clean_title}' [{note['id']}]"


def list_notes(tag: str = "") -> str:
    """List all notes, optionally filtered by *tag*."""
    notes = _load()
    if not notes:
        return "No hay notas guardadas."

    if tag and tag.strip():
        t = tag.strip().lower()
        notes = [n for n in notes if any(t == tg.lower() for tg in n.get("tags", []))]
        if not notes:
            return f"No hay notas con la etiqueta '{tag}'."

    notes_sorted = sorted(notes, key=lambda n: n.get("updated", ""), reverse=True)
    header = f"{len(notes_sorted)} nota(s):"
    return header + "\n" + "\n".join(_fmt_short(n) for n in notes_sorted)


def read_note(title: str) -> str:
    """Read the full content of a note by title (or by id)."""
    query = (title or "").strip()
    if not query:
        return "Indica el título o id de la nota."

    notes = _load()
    note = (
        next((n for n in notes if n["id"] == query), None)
        or next((n for n in notes if n["title"].lower() == query.lower()), None)
        or next((n for n in notes if query.lower() in n["title"].lower()), None)
    )
    if not note:
        return f"No se encontró ninguna nota con título/id '{query}'."

    tags = f"Etiquetas: {', '.join(note['tags'])}\n" if note.get("tags") else ""
    return (
        f"# {note['title']} [{note['id']}]\n"
        f"{tags}"
        f"Creada: {note.get('created', '?')} | Actualizada: {note.get('updated', '?')}\n"
        f"---\n{note.get('content', '')}"
    )


def search_notes(query: str) -> str:
    """Search notes by title or content (case-insensitive)."""
    if not query or not query.strip():
        return "Indica un término de búsqueda."

    q = query.strip().lower()
    notes = _load()
    matches = [
        n for n in notes
        if q in n.get("title", "").lower() or q in n.get("content", "").lower()
    ]
    if not matches:
        return f"No se encontraron notas con '{query}'."

    matches_sorted = sorted(matches, key=lambda n: n.get("updated", ""), reverse=True)
    return f"{len(matches_sorted)} resultado(s) para '{query}':\n" + "\n".join(
        _fmt_short(n) for n in matches_sorted
    )


def delete_note(title: str) -> str:
    """Delete a note by title or id."""
    query = (title or "").strip()
    if not query:
        return "Indica el título o id de la nota a eliminar."

    notes = _load()
    note = (
        next((n for n in notes if n["id"] == query), None)
        or next((n for n in notes if n["title"].lower() == query.lower()), None)
    )
    if not note:
        return f"No se encontró ninguna nota con título/id '{query}'."

    remaining = [n for n in notes if n["id"] != note["id"]]
    _save(remaining)
    return f"Nota '{note['title']}' [{note['id']}] eliminada."
