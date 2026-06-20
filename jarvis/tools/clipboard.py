def get_clipboard() -> str:
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content:
            return "El portapapeles está vacío"
        preview = content if len(content) <= 500 else content[:500] + "..."
        return f"Portapapeles:\n{preview}"
    except ImportError:
        return "pyperclip no instalado. Instala: pip install pyperclip"
    except Exception as e:
        return f"Error al leer portapapeles: {e}"


def set_clipboard(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Texto copiado al portapapeles ({len(text)} caracteres)."
    except ImportError:
        return "pyperclip no instalado. Instala: pip install pyperclip"
    except Exception as e:
        return f"Error al escribir portapapeles: {e}"
