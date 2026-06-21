import platform
import subprocess
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


def web_search(query: str, engine: str = "google") -> str:
    """Open a search query in the browser's incognito/private mode.

    Builds the search URL for the chosen engine and opens it without leaving
    history. Falls back to the default browser if no incognito-capable browser
    is found.
    """
    template = SEARCH_URLS.get(engine, SEARCH_URLS["google"])
    url = template.format(quote(query))
    return _open_incognito(url)
