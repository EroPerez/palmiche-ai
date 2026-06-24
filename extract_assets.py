#!/usr/bin/env python3
"""Extraer icono y audio de bienvenida desde un video de YouTube.

Descarga la miniatura del video como icono PNG y los primeros segundos
de audio como clip de bienvenida MP3.

Requisitos:
    pip install yt-dlp
    apt install ffmpeg      # Linux
    brew install ffmpeg     # macOS

Uso:
    python extract_assets.py

Los archivos se guardan en jarvis/assets/ y se pueden referenciar
desde jarvis/.env:
    JARVIS_TRAY_ICON=jarvis/assets/icon.png
    JARVIS_WELCOME_AUDIO=jarvis/assets/welcome.mp3
"""
import os
import subprocess
import sys
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────────────────────
VIDEO_URL    = "https://www.youtube.com/shorts/NeLnwB4gwJA"
ASSETS_DIR   = Path(__file__).parent / "jarvis" / "assets"
ICON_PATH    = ASSETS_DIR / "icon.png"
WELCOME_PATH = ASSETS_DIR / "welcome.mp3"
CLIP_SECONDS = 6          # segundos iniciales a recortar como clip de voz


def _run(*cmd, check=False):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=check)


def _check_deps():
    missing = []
    for prog in ("yt-dlp", "ffmpeg"):
        if subprocess.run(["which", prog], capture_output=True).returncode != 0:
            missing.append(prog)
    if missing:
        print(f"[ERROR] Faltan dependencias: {', '.join(missing)}")
        print("  Linux:  sudo apt install ffmpeg && pip install yt-dlp")
        print("  macOS:  brew install ffmpeg && pip install yt-dlp")
        sys.exit(1)


def extract_icon():
    """Descarga la miniatura del video y la guarda como icon.png."""
    print("\n[1/2] Descargando miniatura como icono...")
    tmp_dir = ASSETS_DIR / "_thumb"
    tmp_dir.mkdir(exist_ok=True)

    _run(
        "yt-dlp",
        "--write-thumbnail",
        "--convert-thumbnails", "png",
        "--skip-download",
        "-o", str(tmp_dir / "thumb.%(ext)s"),
        VIDEO_URL,
    )

    pngs = list(tmp_dir.glob("*.png")) + list(tmp_dir.glob("*.jpg"))
    if not pngs:
        # Fallback: use ffmpeg to grab frame 0
        print("  Miniatura no disponible, extrayendo frame 0 con ffmpeg...")
        tmp_mp4 = ASSETS_DIR / "_tmp_video.mp4"
        _run("yt-dlp", "-f", "worst[ext=mp4]", "-o", str(tmp_mp4), VIDEO_URL)
        if tmp_mp4.exists():
            _run("ffmpeg", "-y", "-i", str(tmp_mp4),
                 "-vframes", "1", "-q:v", "2", str(ICON_PATH))
            tmp_mp4.unlink(missing_ok=True)
    else:
        src = pngs[0]
        # Resize to 128×128 for use as tray icon
        result = _run("ffmpeg", "-y", "-i", str(src),
                      "-vf", "scale=128:128:force_original_aspect_ratio=decrease,"
                             "pad=128:128:(ow-iw)/2:(oh-ih)/2",
                      str(ICON_PATH))
        for f in tmp_dir.iterdir():
            f.unlink()
        tmp_dir.rmdir()

    if ICON_PATH.exists():
        print(f"  ✓  Icono guardado: {ICON_PATH}")
        return True
    print("  ✗  No se pudo obtener el icono.")
    return False


def extract_audio():
    """Descarga el audio y recorta los primeros CLIP_SECONDS segundos."""
    print(f"\n[2/2] Extrayendo primeros {CLIP_SECONDS}s de audio como voz de bienvenida...")
    tmp_full = ASSETS_DIR / "_audio_full.mp3"

    _run(
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", str(tmp_full),
        VIDEO_URL,
    )

    if not tmp_full.exists():
        print("  ✗  No se pudo descargar el audio.")
        return False

    _run(
        "ffmpeg", "-y",
        "-i", str(tmp_full),
        "-t", str(CLIP_SECONDS),
        "-acodec", "libmp3lame", "-q:a", "2",
        str(WELCOME_PATH),
    )
    tmp_full.unlink(missing_ok=True)

    if WELCOME_PATH.exists():
        print(f"  ✓  Audio de bienvenida guardado: {WELCOME_PATH}")
        return True
    print("  ✗  No se pudo recortar el audio.")
    return False


def print_env_hints(ok_icon, ok_audio):
    print("\n" + "─" * 60)
    print("Agrega estas líneas a  jarvis/.env  para usar los recursos:")
    print("─" * 60)
    if ok_icon:
        print(f"JARVIS_TRAY_ICON={ICON_PATH}")
    if ok_audio:
        print(f"JARVIS_WELCOME_AUDIO={WELCOME_PATH}")
    print("─" * 60 + "\n")


def main():
    print("=" * 60)
    print("  Palmiche J.A.R.V.I.S — extractor de recursos")
    print(f"  Fuente: {VIDEO_URL}")
    print("=" * 60)

    _check_deps()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    ok_icon  = extract_icon()
    ok_audio = extract_audio()
    print_env_hints(ok_icon, ok_audio)


if __name__ == "__main__":
    main()
