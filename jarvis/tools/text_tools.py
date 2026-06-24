"""Text analysis and transformation utilities for Jarvis."""
import re
import unicodedata


def text_stats(text: str) -> str:
    """Count words, characters, lines, sentences, and estimate reading time."""
    if not text:
        return "Texto vacío."

    lines = text.split("\n")
    words = text.split()
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    sentences = len(re.findall(r"[.!?]+", text)) or 1
    paragraphs = len([l for l in lines if l.strip()])
    # Average reading speed: 200 words/min
    reading_secs = max(1, len(words) * 60 // 200)
    reading_str = f"{reading_secs // 60}m {reading_secs % 60}s" if reading_secs >= 60 else f"{reading_secs}s"

    return (
        f"Palabras:       {len(words)}\n"
        f"Caracteres:     {chars} ({chars_no_spaces} sin espacios)\n"
        f"Líneas:         {len(lines)}\n"
        f"Párrafos:       {paragraphs}\n"
        f"Oraciones:      {sentences}\n"
        f"Tiempo lectura: ~{reading_str}"
    )


def text_transform(text: str, operation: str) -> str:
    """Apply a transformation to *text*.

    Operations: upper, lower, title, capitalize, reverse, slug, camel, snake,
    trim, strip_accents, count_vowels, palindrome.
    """
    op = (operation or "").strip().lower()

    if op == "upper":
        return text.upper()
    if op == "lower":
        return text.lower()
    if op == "title":
        return text.title()
    if op == "capitalize":
        return text.capitalize()
    if op == "reverse":
        return text[::-1]
    if op == "trim":
        return text.strip()
    if op in ("slug", "kebab"):
        normalized = unicodedata.normalize("NFD", text.lower())
        ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    if op == "snake":
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip())
        return re.sub(r"([a-z])([A-Z])", r"\1_\2", slug).lower().strip("_")
    if op == "camel":
        words = re.split(r"[\s_\-]+", text.strip())
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])
    if op == "pascal":
        words = re.split(r"[\s_\-]+", text.strip())
        return "".join(w.capitalize() for w in words)
    if op == "strip_accents":
        normalized = unicodedata.normalize("NFD", text)
        return "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    if op in ("count_vowels", "vowels"):
        count = sum(1 for c in text.lower() if c in "aeiouáéíóúàèìòùäëïöü")
        return f"Vocales en el texto: {count}"
    if op in ("palindrome", "is_palindrome"):
        clean = re.sub(r"[^a-zA-Z0-9áéíóúñüÁÉÍÓÚÑÜ]", "", text.lower())
        is_pal = clean == clean[::-1]
        return f"{'✓ Es' if is_pal else '✗ No es'} palíndromo ('{clean}')"
    if op in ("count_words",):
        return f"Palabras: {len(text.split())}"

    available = (
        "upper, lower, title, capitalize, reverse, trim, slug, snake, camel, pascal, "
        "strip_accents, count_vowels, palindrome"
    )
    return f"Operación '{operation}' no reconocida. Disponibles: {available}"
