import subprocess
from pathlib import Path

from ..config import JARVIS_SUDO_PASSWORD

_PERMISSION_PATTERNS = (
    "permission denied",
    "access denied",
    "operation not permitted",
    "not permitted",
    "you must be root",
    "requires root",
    "run this program with root privileges",
    "must be superuser",
    "must be run as root",
    "insufficient privileges",
    "need to be root",
    "eacces",
    "eperm",
)


def _is_permission_error(output: str) -> bool:
    """Return True if *output* looks like a permission / privilege error."""
    lower = output.lower()
    return any(p in lower for p in _PERMISSION_PATTERNS)


def _needs_sudo(command: str) -> bool:
    """Return True if *command* starts with or contains a sudo invocation."""
    stripped = command.lstrip()
    if stripped.startswith("sudo "):
        return True
    for sep in ("&&", "||", ";", "|"):
        for part in command.split(sep):
            if part.strip().startswith("sudo "):
                return True
    return False


def _run(command: str, cwd: str, stdin_data: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
        input=stdin_data,
    )


def _format_output(result: subprocess.CompletedProcess, hide_sudo_prompt: bool = False) -> str:
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        stderr_clean = result.stderr
        if hide_sudo_prompt:
            stderr_clean = "\n".join(
                line for line in stderr_clean.splitlines()
                if "[sudo]" not in line and "Password" not in line
            )
        if stderr_clean.strip():
            output += ("\n" if output else "") + f"[stderr] {stderr_clean}"
    if not output.strip():
        return f"Comando ejecutado. Código de retorno: {result.returncode}"
    if len(output) > 2000:
        output = output[:2000] + "\n... (truncado)"
    return output.strip()


def run_shell_command(command: str, working_dir: str = "~", use_sudo: bool = False) -> str:
    """Run *command* in a shell with a 30-second timeout and return stdout/stderr output.

    If the command already contains ``sudo`` and ``JARVIS_SUDO_PASSWORD`` is
    configured, the password is fed automatically via ``sudo -S``.

    When *use_sudo* is True the command is prefixed with ``sudo -S`` and the
    stored password is piped in (requires ``JARVIS_SUDO_PASSWORD``).

    If the command fails with a permission error and ``JARVIS_SUDO_PASSWORD``
    is configured, the response tells the agent so it can offer to retry with
    ``use_sudo=true``.
    """
    cwd = Path(working_dir).expanduser()
    if not cwd.exists():
        cwd = Path.home()

    stdin_data = None
    actual_command = command

    if use_sudo:
        if not JARVIS_SUDO_PASSWORD:
            return (
                "Error: se solicitó use_sudo=true pero JARVIS_SUDO_PASSWORD no está configurada. "
                "El usuario puede definirla en el archivo .env."
            )
        actual_command = f"sudo -S {command}"
        stdin_data = JARVIS_SUDO_PASSWORD + "\n"
    elif _needs_sudo(command) and JARVIS_SUDO_PASSWORD:
        actual_command = command.replace("sudo ", "sudo -S ", 1)
        stdin_data = JARVIS_SUDO_PASSWORD + "\n"

    try:
        result = _run(actual_command, str(cwd), stdin_data)

        combined = (result.stdout or "") + (result.stderr or "")

        if result.returncode != 0 and not use_sudo and not _needs_sudo(command) and _is_permission_error(combined):
            hint = ""
            if JARVIS_SUDO_PASSWORD:
                hint = (
                    " JARVIS_SUDO_PASSWORD está configurada: puedes reintentar "
                    "esta herramienta con use_sudo=true para ejecutar con privilegios elevados."
                )
            else:
                hint = (
                    " JARVIS_SUDO_PASSWORD no está configurada. "
                    "El usuario puede definirla en .env para permitir reintento automático con sudo."
                )

            output = _format_output(result)
            return (
                f"{output}\n\n⚠️ El comando falló por falta de permisos.{hint} "
                "Informa al usuario y pregunta si desea reintentar con privilegios elevados (sudo)."
            )

        return _format_output(result, hide_sudo_prompt=bool(stdin_data))

    except subprocess.TimeoutExpired:
        return "Error: el comando superó el límite de 30 segundos"
    except Exception as e:
        return f"Error ejecutando comando: {e}"
