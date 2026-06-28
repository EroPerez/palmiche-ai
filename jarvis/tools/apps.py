import platform
import subprocess
from typing import Optional
import psutil


def open_application(name: str) -> str:
    """Launch an application by name or command using the OS default mechanism."""
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.Popen(
                [name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif system == "Darwin":
            subprocess.Popen(
                ["open", "-a", name] if not name.startswith("/") else ["open", name]
            )
        else:
            return f"Sistema operativo no soportado para abrir aplicaciones: {system}"
        return f"Abriendo {name}..."
    except FileNotFoundError:
        return f"Aplicación '{name}' no encontrada. Verifica que esté instalada y en el PATH."
    except Exception as e:
        return f"No se pudo abrir '{name}': {e}"


def close_application(name: str, force: bool = False) -> str:
    """Terminate all processes whose name contains *name*; use SIGKILL if force=True."""
    target = name.strip()
    if not target:
        return "Nombre de proceso inválido: no puede estar vacío"

    target_lower = target.lower()
    killed = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc_name = proc.info.get("name") or ""
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if target_lower in proc_name.lower() or target_lower in cmdline.lower():
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                killed.append(f"{proc_name} (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not killed:
        return f"No se encontró ningún proceso con nombre '{target}'"
    action = "Forzado a cerrar" if force else "Cerrado"
    return f"{action}: {', '.join(killed)}"


def list_running_apps(filter_str: Optional[str] = None) -> str:
    """List running processes sorted by RAM usage, optionally filtered by name substring."""
    processes = {}
    for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
        try:
            pname = proc.info["name"]
            if filter_str and filter_str.lower() not in pname.lower():
                continue
            mem = proc.info["memory_percent"] or 0.0
            if pname not in processes:
                processes[pname] = {"count": 0, "mem": 0.0, "pid": proc.info["pid"]}
            processes[pname]["count"] += 1
            processes[pname]["mem"] += mem
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    sorted_procs = sorted(processes.items(), key=lambda x: x[1]["mem"], reverse=True)
    lines = ["Procesos en ejecución (por uso de RAM):"]
    for pname, info in sorted_procs[:20]:
        count_str = f" (x{info['count']})" if info["count"] > 1 else ""
        lines.append(
            f"  {pname + count_str:<35} PID: {info['pid']:<8} RAM: {info['mem']:.1f}%"
        )
    return "\n".join(lines)
