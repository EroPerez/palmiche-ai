import platform
import subprocess
from urllib.parse import quote

SEARCH_URLS = {
    "google": "https://www.google.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
    "youtube": "https://www.youtube.com/results?search_query={}",
}

_DDG_API = "https://api.duckduckgo.com/"
_HEADERS = {"User-Agent": "palmiche-jarvis/1.0"}


def open_url(url: str) -> str:
    """Open *url* in the system default browser, prepending https:// if no scheme given."""
    if not url.startswith(("http://", "https://", "ftp://")):
        url = "https://" + url
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.Popen(["xdg-open", url])
        elif system == "Darwin":
            subprocess.Popen(["open", url])
        return f"Abriendo en navegador: {url}"
    except Exception as e:
        return f"Error al abrir URL: {e}"


def web_search(query: str, engine: str = "duckduckgo") -> str:
    """Search the web and return results as text — no browser is opened.

    For YouTube searches the search URL is returned; use open_url to open it.
    Google and DuckDuckGo queries are resolved via the DuckDuckGo Instant
    Answer API using the existing ``requests`` dependency.
    """
    import requests

    if engine == "youtube":
        url = SEARCH_URLS["youtube"].format(quote(query))
        return (
            f"Búsqueda en YouTube: {url}\n"
            "Usa open_url para abrir en el navegador."
        )

    try:
        resp = requests.get(
            _DDG_API,
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return f"Error al buscar: {exc}"

    lines = []

    abstract = data.get("AbstractText", "").strip()
    if abstract:
        lines.append(abstract)
        source = data.get("AbstractSource", "")
        src_url = data.get("AbstractURL", "")
        if source:
            lines.append(f"Fuente: {source} — {src_url}")

    for topic in data.get("RelatedTopics", [])[:6]:
        if not isinstance(topic, dict):
            continue
        text = topic.get("Text", "").strip()
        link = topic.get("FirstURL", "")
        if text:
            lines.append(f"• {text}")
        if link:
            lines.append(f"  {link}")

    if not lines:
        url = SEARCH_URLS["duckduckgo"].format(quote(query))
        return (
            f"Sin resultados instantáneos para «{query}».\n"
            f"Búsqueda: {url}\n"
            "Usa open_url para abrir en el navegador."
        )

    return "\n".join(lines)
