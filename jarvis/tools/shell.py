import subprocess
from pathlib import Path

from ..config import JARVIS_SUDO_PASSWORD


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


def run_shell_command(command: str, working_dir: str = "~") -> str:
    """Run *command* in a shell with a 30-second timeout and return stdout/stderr output.

    If the command uses ``sudo`` and ``JARVIS_SUDO_PASSWORD`` is configured,
    the password is fed automatically via ``sudo -S``.
    """
    cwd = Path(working_dir).expanduser()
    if not cwd.exists():
        cwd = Path.home()

    stdin_data = None
    actual_command = command

    if _needs_sudo(command) and JARVIS_SUDO_PASSWORD:
        actual_command = command.replace("sudo ", "sudo -S ", 1)
        stdin_data = JARVIS_SUDO_PASSWORD + "\n"

    try:
        result = subprocess.run(
            actual_command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=30,
            input=stdin_data,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            stderr_clean = result.stderr
            if stdin_data:
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
    except subprocess.TimeoutExpired:
        return "Error: el comando superó el límite de 30 segundos"
    except Exception as e:
        return f"Error ejecutando comando: {e}"
