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


def _snap_name_from_cmdline(cmdline_list: list[str]) -> str | None:
    """Extract the snap package name from a process cmdline, or None if not a snap process."""
    for arg in cmdline_list:
        if arg.startswith("/snap/"):
            parts = arg.split("/")
            if len(parts) > 2 and parts[2]:
                return parts[2]
    return None


def _stop_snap(snap_name: str) -> str:
    """Stop a snap package and return a status string."""
    try:
        result = subprocess.run(
            ["snap", "stop", snap_name],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return f"snap:{snap_name} detenido"
        return f"snap:{snap_name} falló — {result.stderr.strip()}"
    except FileNotFoundError:
        return f"snap:{snap_name} — comando 'snap' no encontrado"
    except Exception as e:
        return f"snap:{snap_name} error — {e}"


def close_application(name: str, force: bool = False) -> str:
    """Terminate all processes whose name contains *name*; use SIGKILL if force=True.

    Snap-confined processes that cannot be killed directly are stopped via
    ``snap stop <package>`` instead.
    """
    target = name.strip()
    if not target:
        return "Nombre de proceso inválido: no puede estar vacío"

    target_lower = target.lower()
    killed = []
    snap_names: set[str] = set()

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc_name = proc.info.get("name") or ""
            cmdline_list = proc.info.get("cmdline") or []
            cmdline = " ".join(cmdline_list)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        if target_lower not in proc_name.lower() and target_lower not in cmdline.lower():
            continue

        snap = _snap_name_from_cmdline(cmdline_list)
        if snap:
            snap_names.add(snap)

        try:
            if force:
                proc.kill()
            else:
                proc.terminate()
            killed.append(f"{proc_name} (PID {proc.info['pid']})")
        except psutil.AccessDenied:
            # snap-confined process; handled below via snap stop
            pass
        except psutil.NoSuchProcess:
            pass

    snap_results = [_stop_snap(s) for s in snap_names]

    if not killed and not snap_results:
        return f"No se encontró ningún proceso con nombre '{target}'"

    parts = []
    if killed:
        action = "Forzado a cerrar" if force else "Cerrado"
        parts.append(f"{action}: {', '.join(killed)}")
    if snap_results:
        parts.append("; ".join(snap_results))
    return "\n".join(parts)


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
