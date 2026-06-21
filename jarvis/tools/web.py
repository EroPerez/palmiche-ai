import platform
import subprocess
from urllib.parse import quote

SEARCH_URLS = {
    "google": "https://www.google.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
    "youtube": "https://www.youtube.com/results?search_query={}",
}

# Browsers tried in order on Linux: (binary, incognito_flag)
_BROWSERS_LINUX = [
    ("google-chrome",        "--incognito"),
    ("google-chrome-stable", "--incognito"),
    ("chromium-browser",     "--incognito"),
    ("chromium",             "--incognito"),
    ("brave-browser",        "--incognito"),
    ("microsoft-edge",       "--inprivate"),
    ("firefox",              "--private-window"),
]

# App names tried in order on macOS: (app_name, incognito_flag)
_BROWSERS_MACOS = [
    ("Google Chrome",   "--incognito"),
    ("Chromium",        "--incognito"),
    ("Brave Browser",   "--incognito"),
    ("Microsoft Edge",  "--inprivate"),
    ("Firefox",         "--private-window"),
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
        for binary, flag in _BROWSERS_LINUX:
            try:
                subprocess.Popen([binary, flag, url])
                return f"Abriendo en modo incógnito: {url}"
            except FileNotFoundError:
                continue

    elif system == "Darwin":
        for app, flag in _BROWSERS_MACOS:
            try:
                subprocess.Popen(["open", "-a", app, "--args", flag, url])
                return f"Abriendo en modo incógnito: {url}"
            except FileNotFoundError:
                continue

    # No incognito-capable browser found — fall back to default browser
    return open_url(url)


def web_search(query: str, engine: str = "google") -> str:
    """Open a search query in the browser's incognito/private mode.

    Builds the search URL for the chosen engine and opens it without leaving
    history. Falls back to the default browser if no incognito-capable browser
    is found.
    """
    template = SEARCH_URLS.get(engine, SEARCH_URLS["google"])
    url = template.format(quote(query))
    return _open_incognito(url)
