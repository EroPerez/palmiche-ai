"""Developer utility tools for Jarvis.

A grab-bag of small, offline-friendly helpers commonly needed while coding:
JSON formatting, hashing, base64/url/hex encoding, UUID generation, timestamp
conversion, HTTP requests, git status, and port inspection.
"""
import base64
import binascii
import hashlib
import json
import subprocess
import urllib.parse
import uuid
from datetime import datetime, timezone
from pathlib import Path


def format_json(text: str, indent: int = 2) -> str:
    """Validate and pretty-print a JSON string with the given indentation."""
    try:
        indent = int(indent)
    except (TypeError, ValueError):
        indent = 2
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return f"JSON inválido: {exc}"
    return json.dumps(parsed, ensure_ascii=False, indent=max(0, indent), sort_keys=False)


def hash_text(text: str, algorithm: str = "sha256") -> str:
    """Compute a hex digest of *text* using md5, sha1, sha256 or sha512."""
    algo = (algorithm or "sha256").strip().lower()
    if algo not in ("md5", "sha1", "sha256", "sha512"):
        return f"Algoritmo no soportado: '{algorithm}'. Usa md5, sha1, sha256 o sha512."
    digest = hashlib.new(algo, text.encode("utf-8")).hexdigest()
    return f"{algo}: {digest}"


def encode_decode(text: str, scheme: str = "base64", operation: str = "encode") -> str:
    """Encode or decode *text* using base64, url or hex."""
    sch = (scheme or "base64").strip().lower()
    op = (operation or "encode").strip().lower()
    if op not in ("encode", "decode"):
        return f"Operación inválida: '{operation}'. Usa 'encode' o 'decode'."
    try:
        if sch == "base64":
            if op == "encode":
                return base64.b64encode(text.encode("utf-8")).decode("ascii")
            return base64.b64decode(text.encode("ascii")).decode("utf-8")
        if sch == "url":
            return urllib.parse.quote(text) if op == "encode" else urllib.parse.unquote(text)
        if sch == "hex":
            if op == "encode":
                return text.encode("utf-8").hex()
            return bytes.fromhex(text.strip()).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        return f"No se pudo {op} con {sch}: {exc}"
    return f"Esquema no soportado: '{scheme}'. Usa base64, url o hex."


def generate_uuid(count: int = 1) -> str:
    """Generate one or more random UUID4 values."""
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 1
    count = max(1, min(50, count))
    return "\n".join(str(uuid.uuid4()) for _ in range(count))


def convert_timestamp(value: str = "now") -> str:
    """Convert between Unix epoch seconds and ISO-8601. 'now' returns the current time."""
    v = (value or "now").strip().lower()
    if v == "now":
        now = datetime.now(timezone.utc)
        return f"epoch: {int(now.timestamp())}\nutc:   {now.isoformat(timespec='seconds')}"
    # Numeric → treat as epoch seconds (or milliseconds if very large)
    try:
        num = float(v)
        if num > 1e12:  # looks like milliseconds
            num /= 1000.0
        dt = datetime.fromtimestamp(num, tz=timezone.utc)
        return f"epoch {int(num)} → {dt.isoformat(timespec='seconds')}"
    except (ValueError, OverflowError, OSError):
        pass
    # Otherwise → treat as ISO datetime
    try:
        dt = datetime.fromisoformat(value.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return f"{value.strip()} → epoch {int(dt.timestamp())}"
    except ValueError:
        return f"No se pudo interpretar '{value}'. Usa epoch (número) o ISO-8601, o 'now'."


def http_request(url: str, method: str = "GET", body: str = "") -> str:
    """Make an HTTP request and return status, key headers, and a body preview."""
    try:
        import requests
    except ImportError:
        return "requests no instalado. Instala: pip install requests"

    m = (method or "GET").strip().upper()
    if m not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"):
        return f"Método HTTP no soportado: '{method}'."
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        kwargs = {"timeout": 15}
        if body and m in ("POST", "PUT", "PATCH", "DELETE"):
            kwargs["data"] = body.encode("utf-8")
        resp = requests.request(m, url, **kwargs)
    except requests.RequestException as exc:
        return f"Error en la petición: {exc}"

    ctype = resp.headers.get("Content-Type", "?")
    preview = resp.text if len(resp.text) <= 1000 else resp.text[:1000] + "\n... (truncado)"
    return (
        f"{m} {url}\n"
        f"Status: {resp.status_code} {resp.reason}\n"
        f"Content-Type: {ctype}  ({len(resp.content)} bytes)\n"
        f"---\n{preview}"
    )


def git_status(path: str = ".") -> str:
    """Show branch, working-tree status and the last commits of a git repository."""
    repo = str(Path(path).expanduser())

    def _git(args: list) -> tuple:
        try:
            r = subprocess.run(
                ["git", "-C", repo, *args],
                capture_output=True, text=True, timeout=15,
            )
            return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
        except FileNotFoundError:
            return 127, "", "git no está instalado"
        except subprocess.TimeoutExpired:
            return 124, "", "git tardó demasiado"

    code, branch, err = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    if code != 0:
        return f"No es un repositorio git válido ({repo}): {err or 'desconocido'}"

    _, status, _ = _git(["status", "--short"])
    _, log, _ = _git(["log", "-5", "--pretty=format:%h %s (%cr)"])

    lines = [f"Repo: {repo}", f"Rama: {branch}"]
    lines.append("Cambios:\n" + (status or "  (árbol limpio)"))
    lines.append("Últimos commits:\n" + (log or "  (sin commits)"))
    return "\n".join(lines)


def find_process_on_port(port: int) -> str:
    """Find which process is listening on *port* (TCP)."""
    try:
        port = int(port)
    except (TypeError, ValueError):
        return f"Puerto inválido: '{port}'."

    try:
        import psutil
    except ImportError:
        return "psutil no instalado. Instala: pip install psutil"

    matches = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            pname = "?"
            if conn.pid:
                try:
                    pname = psutil.Process(conn.pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pname = "?"
            matches.append(f"PID {conn.pid} ({pname}) escuchando en {conn.laddr.ip}:{port}")

    if not matches:
        return f"Ningún proceso escuchando en el puerto {port}."
    return "\n".join(matches)
