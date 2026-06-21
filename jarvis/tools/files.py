import subprocess
from pathlib import Path
from typing import Optional
import platform


def search_files(
    pattern: str, directory: str = "~", file_type: str = "any"
) -> str:
    """Search for files or directories matching *pattern* under *directory* (max depth 6)."""
    search_dir = Path(directory).expanduser()
    if not search_dir.exists():
        return f"Directorio '{directory}' no encontrado"

    type_flag = []
    if file_type == "file":
        type_flag = ["-type", "f"]
    elif file_type == "directory":
        type_flag = ["-type", "d"]

    try:
        cmd = [
            "find", str(search_dir),
            "-maxdepth", "6",
            "-iname", f"*{pattern}*",
        ] + type_flag
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = [l for l in result.stdout.strip().split("\n") if l]
        if not lines:
            return f"No se encontraron elementos con patrón '{pattern}' en {directory}"
        total = len(lines)
        shown = lines[:20]
        out = f"Encontrado(s): {total} resultado(s)\n"
        out += "\n".join(f"  {l}" for l in shown)
        if total > 20:
            out += f"\n  ... y {total - 20} más"
        return out
    except subprocess.TimeoutExpired:
        return "Búsqueda tardó demasiado. Especifica un directorio más concreto."
    except Exception as e:
        return f"Error en búsqueda: {e}"


def open_file(path: str) -> str:
    """Open *path* with the system default application (xdg-open / open)."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return f"Archivo '{path}' no encontrado"
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.Popen(["xdg-open", str(file_path)])
        elif system == "Darwin":
            subprocess.Popen(["open", str(file_path)])
        return f"Abriendo {file_path.name}..."
    except Exception as e:
        return f"Error al abrir '{path}': {e}"


def list_directory(path: str = "~", show_hidden: bool = False) -> str:
    """List files and subdirectories in *path*, sorted dirs first then files by name."""
    dir_path = Path(path).expanduser()
    if not dir_path.exists():
        return f"'{path}' no existe"
    if not dir_path.is_dir():
        return f"'{path}' no es un directorio"
    try:
        items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        if not show_hidden:
            items = [i for i in items if not i.name.startswith(".")]
        lines = [f"Contenido de {dir_path}:"]
        for item in items[:40]:
            if item.is_dir():
                lines.append(f"  [DIR]  {item.name}/")
            else:
                size = item.stat().st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024**2:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / 1024**2:.1f} MB"
                lines.append(f"  [FILE] {item.name:<42} {size_str:>10}")
        if len(items) > 40:
            lines.append(f"  ... y {len(items) - 40} elementos más")
        return "\n".join(lines)
    except PermissionError:
        return f"Sin permiso para leer '{path}'"


def read_file(path: str, max_lines: int = 100) -> str:
    """Read up to *max_lines* lines of a text file and return the content."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return f"Archivo '{path}' no encontrado"
    if not file_path.is_file():
        return f"'{path}' no es un archivo"
    try:
        collected = []
        truncated = False
        with file_path.open("r", encoding="utf-8", errors="replace") as fh:
            for idx, line in enumerate(fh):
                if idx >= max_lines:
                    truncated = True
                    break
                collected.append(line.rstrip("\n"))
        snippet = "\n".join(collected)
        result = f"--- {file_path.name} ---\n{snippet}"
        if truncated:
            result += f"\n\n[... truncado a {max_lines} líneas]"
        return result
    except Exception as e:
        return f"Error al leer '{path}': {e}"


def create_directory(path: str) -> str:
    """Create *path* and any missing parent directories."""
    dir_path = Path(path).expanduser()
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return f"Directorio creado: {dir_path}"
    except Exception as e:
        return f"Error al crear directorio: {e}"


def write_file(path: str, content: str, mode: str = "write") -> str:
    """Escribe o agrega contenido en un archivo de texto.

    Args:
        path: Ruta del archivo de destino.
        content: Contenido a escribir.
        mode: 'write' para sobreescribir (default) o 'append' para añadir al final.
    """
    file_path = Path(path).expanduser()
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "append":
            with file_path.open("a", encoding="utf-8") as f:
                f.write(content)
            return f"Contenido añadido a: {file_path} ({len(content)} caracteres)"
        else:
            file_path.write_text(content, encoding="utf-8")
            return f"Archivo escrito: {file_path} ({len(content)} caracteres)"
    except Exception as e:
        return f"Error al escribir '{path}': {e}"


def delete_file(path: str) -> str:
    """Elimina un archivo o directorio vacío.

    Args:
        path: Ruta del archivo o directorio a eliminar.
    """
    target = Path(path).expanduser()
    if not target.exists():
        return f"'{path}' no existe"
    try:
        if target.is_file():
            target.unlink()
            return f"Archivo eliminado: {target}"
        elif target.is_dir():
            target.rmdir()
            return f"Directorio vacío eliminado: {target}"
        return f"'{path}' no es un archivo ni directorio"
    except OSError as e:
        return f"Error al eliminar '{path}': {e}"


def move_file(source: str, destination: str) -> str:
    """Mueve o renombra un archivo o directorio.

    Args:
        source: Ruta de origen.
        destination: Ruta de destino.
    """
    import shutil
    src = Path(source).expanduser()
    dst = Path(destination).expanduser()
    if not src.exists():
        return f"Origen '{source}' no existe"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"Movido: {src} → {dst}"
    except Exception as e:
        return f"Error al mover '{source}': {e}"


def copy_file(source: str, destination: str) -> str:
    """Copia un archivo o directorio.

    Args:
        source: Ruta de origen.
        destination: Ruta de destino.
    """
    import shutil
    src = Path(source).expanduser()
    dst = Path(destination).expanduser()
    if not src.exists():
        return f"Origen '{source}' no existe"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(str(src), str(dst))
        else:
            shutil.copy2(str(src), str(dst))
        return f"Copiado: {src} → {dst}"
    except Exception as e:
        return f"Error al copiar '{source}': {e}"
