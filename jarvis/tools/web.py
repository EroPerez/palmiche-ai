import html
import html.parser
import platform
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import quote

SEARCH_URLS = {
    "google": "https://www.google.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
    "youtube": "https://www.youtube.com/results?search_query={}",
}

# Browsers tried in order on Linux: (binary, incognito_args)
# Chromium-family browsers need --new-window: with only --incognito they reuse
# an already-open incognito window and add a tab instead of opening a new window.
# Firefox's --private-window already opens a fresh private window each time.
_BROWSERS_LINUX = [
    ("google-chrome",        ["--incognito", "--new-window"]),
    ("google-chrome-stable", ["--incognito", "--new-window"]),
    ("chromium-browser",     ["--incognito", "--new-window"]),
    ("chromium",             ["--incognito", "--new-window"]),
    ("brave-browser",        ["--incognito", "--new-window"]),
    ("microsoft-edge",       ["--inprivate", "--new-window"]),
    ("firefox",              ["--private-window"]),
]

# App names tried in order on macOS: (app_name, incognito_args)
_BROWSERS_MACOS = [
    ("Google Chrome",   ["--incognito", "--new-window"]),
    ("Chromium",        ["--incognito", "--new-window"]),
    ("Brave Browser",   ["--incognito", "--new-window"]),
    ("Microsoft Edge",  ["--inprivate", "--new-window"]),
    ("Firefox",         ["--private-window"]),
]


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


def _open_incognito(url: str) -> str:
    """Open *url* in the first available browser's incognito/private mode."""
    system = platform.system()

    if system == "Linux":
        for binary, args in _BROWSERS_LINUX:
            try:
                subprocess.Popen(
                    [binary, *args, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return f"Abriendo en modo incógnito: {url}"
            except FileNotFoundError:
                continue

    elif system == "Darwin":
        for app, args in _BROWSERS_MACOS:
            try:
                # -n launches a new instance so the flags/URL are honored even
                # when the browser is already running (otherwise `open` just
                # activates the existing window and ignores --args).
                subprocess.Popen(["open", "-na", app, "--args", *args, url])
                return f"Abriendo en modo incógnito: {url}"
            except FileNotFoundError:
                continue

    # No incognito-capable browser found — fall back to default browser
    return open_url(url)


class _TextExtractor(html.parser.HTMLParser):
    """Minimal HTML → plain-text extractor (stdlib only, no BeautifulSoup needed)."""

    _SKIP_TAGS = {"script", "style", "noscript", "head", "meta", "link", "svg", "iframe"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self._SKIP_TAGS:
            self._skip += 1
        if tag.lower() in ("br", "p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"):
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self._SKIP_TAGS:
            self._skip = max(0, self._skip - 1)

    def handle_data(self, data):
        if self._skip == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self._parts)
        lines = (line.strip() for line in raw.splitlines())
        return "\n".join(line for line in lines if line)


def fetch_webpage(url: str, max_chars: int = 3000) -> str:
    """Fetch a webpage and return its readable text content (stripped of HTML)."""
    try:
        import requests as _req
    except ImportError:
        return "requests no instalado. Instala: pip install requests"

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = _req.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (palmiche-jarvis/1.0)"},
            allow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as exc:
        return f"Error al obtener la página: {exc}"

    ctype = resp.headers.get("Content-Type", "")
    if (
        "text/html" not in ctype
        and "text/plain" not in ctype
        and "application/xhtml+xml" not in ctype
    ):
        return f"Tipo de contenido no soportado: {ctype}"

    try:
        raw_text = resp.text
    except (UnicodeDecodeError, LookupError) as exc:
        return f"Error al decodificar la página: {exc}"

    parser = _TextExtractor()
    try:
        parser.feed(raw_text)
    except Exception as exc:
        return f"Error al parsear el HTML: {exc}"
    text = parser.get_text()

    try:
        limit = int(max_chars)
    except (TypeError, ValueError):
        limit = 3000
    limit = max(500, min(10000, limit))

    if len(text) > limit:
        text = text[:limit] + f"\n\n… (truncado, {len(text) - limit} caracteres más)"

    return f"Fuente: {resp.url}\n---\n{text}"


def get_rss_feed(url: str, max_items: int = 10) -> str:
    """Fetch an RSS or Atom feed and return the latest items with titles and links."""
    try:
        import requests as _req
    except ImportError:
        return "requests no instalado. Instala: pip install requests"

    try:
        limit = max(1, min(50, int(max_items)))
    except (TypeError, ValueError):
        limit = 10

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = _req.get(url, timeout=15, headers={"User-Agent": "palmiche-jarvis/1.0"})
        resp.raise_for_status()
    except Exception as exc:
        return f"Error al obtener el feed: {exc}"

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        return f"Error al parsear el feed XML: {exc}"

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items: list[tuple[str, str, str]] = []

    # RSS 2.0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "Sin título").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        items.append((title, link, pub[:16] if pub else ""))

    # Atom
    if not items:
        for entry in root.findall(".//atom:entry", ns):
            title = (entry.findtext("atom:title", namespaces=ns) or "Sin título").strip()
            link_el = entry.find("atom:link", ns)
            link = (link_el.get("href", "") if link_el is not None else "").strip()
            pub = (entry.findtext("atom:updated", namespaces=ns) or "").strip()
            items.append((title, link, pub[:10] if pub else ""))

    if not items:
        return "No se encontraron entradas en el feed."

    feed_title = root.findtext(".//title") or root.findtext(".//atom:title", namespaces=ns) or url
    lines = [f"Feed: {feed_title.strip()} ({len(items[:limit])} de {len(items)} entradas)"]
    for title, link, pub in items[:limit]:
        date_str = f" [{pub}]" if pub else ""
        lines.append(f"• {title}{date_str}\n  {link}")

    return "\n".join(lines)


def web_search(query: str, engine: str = "google") -> str:
    """Open a search query in the browser's incognito/private mode.

    Builds the search URL for the chosen engine and opens it without leaving
    history. Falls back to the default browser if no incognito-capable browser
    is found.
    """
    template = SEARCH_URLS.get(engine, SEARCH_URLS["google"])
    url = template.format(quote(query))
    return _open_incognito(url)
