"""Centralized audio engine for Jarvis.

Provides a queue-based audio playback system with TTS caching, volume control,
sentence-level streaming, and interrupt support. All audio output (TTS and file
playback) should go through this module.

Requires: pip install gtts pyttsx3 (optional, for TTS tiers 1 and 2)
"""

import hashlib
import logging
import os
import platform
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_TTS_CACHE_DIR = Path(tempfile.gettempdir()) / "jarvis_tts_cache"

_SENTENCE_RE = re.compile(r"(?<=[.!?;])\s+")

_MAX_CACHE_FILES = 200

# ---------------------------------------------------------------------------
# Text preprocessing — strip markdown and emojis before TTS
# ---------------------------------------------------------------------------

_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U0001F1E0-\U0001F1FF"
    "\U00002500-\U00002BEF"
    "\U00002300-\U000023FF"
    "]+",
    flags=re.UNICODE,
)


def clean_for_tts(text: str) -> str:
    """Remove markdown syntax and emojis so TTS reads only natural prose."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_\n]+)_{1,3}", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = _EMOJI_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class AudioEngine:
    """Thread-safe audio engine with queued playback, caching, and interrupts.

    Usage::

        engine = AudioEngine(lang="es", volume=80)
        engine.speak("Hola, ¿en qué puedo ayudarte?")
        engine.play_file("/path/to/welcome.mp3")
        engine.stop()          # interrupt current playback
        engine.shutdown()      # stop and clean up
    """

    def __init__(
        self,
        lang: str = "es",
        volume: int = 100,
        cache_enabled: bool = True,
        stream_sentences: bool = True,
        cache_dir: Optional[Path] = None,
    ):
        self.lang = lang
        self._volume = max(0, min(100, volume))
        self._cache_enabled = cache_enabled
        self._stream_sentences = stream_sentences
        self._cache_dir = cache_dir or _TTS_CACHE_DIR

        self._queue: list[tuple[str, dict]] = []
        self._queue_lock = threading.Lock()
        self._queue_event = threading.Event()
        self._current_process: Optional[subprocess.Popen] = None
        self._process_lock = threading.Lock()
        self._playing = threading.Event()
        self._stopped = threading.Event()
        self._shutdown_event = threading.Event()

        self._worker = threading.Thread(
            target=self._playback_worker, daemon=True, name="jarvis-audio-engine"
        )
        self._worker.start()

        if cache_enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ public

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, value: int):
        self._volume = max(0, min(100, value))

    def speak(self, text: str, block: bool = False) -> None:
        """Enqueue text for TTS playback."""
        text = clean_for_tts(text)
        if not text:
            return

        if self._stream_sentences and len(text) > 120:
            sentences = _SENTENCE_RE.split(text)
            for s in sentences:
                s = s.strip()
                if s:
                    self._enqueue("tts", {"text": s})
        else:
            self._enqueue("tts", {"text": text})

        if block:
            self.wait()

    def speak_async(self, text: str, on_done=None) -> None:
        """Enqueue text for TTS playback with an optional completion callback."""
        text = clean_for_tts(text)
        if not text:
            if on_done:
                on_done()
            return
        self._enqueue("tts", {"text": text, "on_done": on_done})

    def play_file(self, path: str, block: bool = False) -> None:
        """Enqueue an audio file for playback."""
        if not os.path.isfile(path):
            logger.warning("Audio file not found: %s", path)
            return
        self._enqueue("file", {"path": path})
        if block:
            self.wait()

    def play_file_async(self, path: str, on_done=None) -> None:
        """Enqueue an audio file for playback with an optional completion callback."""
        if not os.path.isfile(path):
            logger.warning("Audio file not found: %s", path)
            if on_done:
                on_done()
            return
        self._enqueue("file", {"path": path, "on_done": on_done})

    def stop(self) -> None:
        """Interrupt current playback and clear the queue."""
        with self._queue_lock:
            self._queue.clear()
        self._stopped.set()
        self._kill_current()

    def wait(self) -> None:
        """Block until the queue is empty and the current item finishes."""
        while True:
            with self._queue_lock:
                empty = len(self._queue) == 0
            if empty and not self._is_playing():
                break
            time.sleep(0.05)

    def shutdown(self) -> None:
        """Stop playback and terminate the worker thread."""
        self.stop()
        self._shutdown_event.set()
        self._queue_event.set()

    def is_idle(self) -> bool:
        """Return True if nothing is playing and the queue is empty."""
        with self._queue_lock:
            return len(self._queue) == 0 and not self._is_playing()

    # ---------------------------------------------------- TTS cache management

    def clear_cache(self) -> int:
        """Remove all cached TTS files. Returns number of files deleted."""
        count = 0
        if self._cache_dir.exists():
            for f in self._cache_dir.iterdir():
                try:
                    f.unlink()
                    count += 1
                except OSError:
                    pass
        return count

    def cache_stats(self) -> dict:
        """Return cache statistics: file count and total size in bytes."""
        if not self._cache_dir.exists():
            return {"files": 0, "size_bytes": 0}
        files = list(self._cache_dir.iterdir())
        total = sum(f.stat().st_size for f in files if f.is_file())
        return {"files": len(files), "size_bytes": total}

    # ----------------------------------------------------------- internal queue

    def _enqueue(self, kind: str, data: dict) -> None:
        with self._queue_lock:
            self._queue.append((kind, data))
        self._queue_event.set()

    def _dequeue(self) -> Optional[tuple[str, dict]]:
        with self._queue_lock:
            return self._queue.pop(0) if self._queue else None

    # ---------------------------------------------------------- playback worker

    def _playback_worker(self) -> None:
        while not self._shutdown_event.is_set():
            self._queue_event.wait(timeout=0.5)
            self._queue_event.clear()
            self._stopped.clear()

            while not self._shutdown_event.is_set():
                item = self._dequeue()
                if item is None:
                    break
                if self._stopped.is_set():
                    break

                kind, data = item
                on_done = data.pop("on_done", None)
                self._playing.set()
                try:
                    if kind == "tts":
                        self._play_tts(data["text"])
                    elif kind == "file":
                        self._play_file_internal(data["path"])
                except Exception as exc:
                    logger.debug("Audio playback error: %s", exc)
                finally:
                    self._playing.clear()
                    if on_done:
                        try:
                            on_done()
                        except Exception:
                            pass

    # ------------------------------------------------------------- TTS helpers

    def _cache_key(self, text: str) -> str:
        raw = f"{text}|{self.lang}".encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def _get_cached(self, text: str) -> Optional[str]:
        if not self._cache_enabled:
            return None
        key = self._cache_key(text)
        path = self._cache_dir / f"{key}.mp3"
        if path.is_file():
            path.touch()
            return str(path)
        return None

    def _put_cache(self, text: str, mp3_path: str) -> str:
        """Copy mp3_path into the cache dir. Returns the cached file path."""
        if not self._cache_enabled:
            return mp3_path
        key = self._cache_key(text)
        dest = self._cache_dir / f"{key}.mp3"
        try:
            if not dest.exists():
                import shutil
                shutil.copy2(mp3_path, dest)
            self._evict_cache()
        except OSError as exc:
            logger.debug("Cache write failed: %s", exc)
        return str(dest)

    def _evict_cache(self) -> None:
        try:
            files = sorted(
                self._cache_dir.iterdir(), key=lambda f: f.stat().st_mtime
            )
            while len(files) > _MAX_CACHE_FILES:
                files.pop(0).unlink(missing_ok=True)
        except OSError:
            pass

    def _play_tts(self, text: str) -> None:
        cached = self._get_cached(text)
        if cached:
            self._play_file_internal(cached)
            return

        # Tier 1: gTTS
        mp3 = self._tts_gtts(text)
        if mp3:
            cached_path = self._put_cache(text, mp3)
            play_path = cached_path if self._cache_enabled and os.path.isfile(cached_path) else mp3
            self._play_file_internal(play_path)
            try:
                os.unlink(mp3)
            except OSError:
                pass
            return

        # Tier 2: pyttsx3
        if self._tts_pyttsx3(text):
            return

        # Tier 3: system TTS
        self._tts_system(text)

    def _tts_gtts(self, text: str) -> Optional[str]:
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang=self.lang, slow=False)
            fd, path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            tts.save(path)
            return path
        except Exception:
            return None

    def _tts_pyttsx3(self, text: str) -> bool:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            voices = engine.getProperty("voices") or []
            for v in voices:
                vid = (v.id or "").lower()
                vname = (v.name or "").lower()
                if "es" in vid or "spanish" in vname or "español" in vname:
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate", 135)
            engine.setProperty("volume", self._volume / 100.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            return True
        except Exception:
            return False

    def _tts_system(self, text: str) -> None:
        system = platform.system()
        try:
            if system == "Linux":
                amp = str(max(1, int(200 * self._volume / 100)))
                proc = subprocess.Popen(
                    ["espeak-ng", "-v", self.lang, "-s", "130", "-p", "40", "-a", amp, text],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                with self._process_lock:
                    self._current_process = proc
                proc.wait()
                with self._process_lock:
                    self._current_process = None
            elif system == "Darwin":
                proc = subprocess.Popen(
                    ["say", "-v", "Monica", text],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                with self._process_lock:
                    self._current_process = proc
                proc.wait()
                with self._process_lock:
                    self._current_process = None
        except FileNotFoundError:
            pass

    # --------------------------------------------------------- file playback

    def _play_file_internal(self, path: str) -> None:
        ext = os.path.splitext(path)[1].lower()
        vol_pct = self._volume

        candidates = []
        if ext == ".mp3":
            candidates.append(["mpg123", "-q", "-f", str(int(32768 * vol_pct / 100)), path])
        else:
            candidates.append(["mpg123", "-q", path])

        candidates.append([
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            "-volume", str(vol_pct), path,
        ])
        candidates.append(["cvlc", "--play-and-exit", "--quiet", path])

        if ext in (".wav", ".ogg"):
            candidates.extend([["paplay", path], ["aplay", path]])

        for cmd in candidates:
            if self._stopped.is_set():
                return
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with self._process_lock:
                    self._current_process = proc
                proc.wait()
                with self._process_lock:
                    self._current_process = None
                if proc.returncode == 0:
                    return
            except FileNotFoundError:
                continue
            except Exception:
                with self._process_lock:
                    self._current_process = None

    def _kill_current(self) -> None:
        with self._process_lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                except OSError:
                    pass

    def _is_playing(self) -> bool:
        with self._process_lock:
            if self._current_process is not None and self._current_process.poll() is None:
                return True
        return self._playing.is_set()


# ---------------------------------------------------------------------------
# Module-level singleton for easy access
# ---------------------------------------------------------------------------

_engine: Optional[AudioEngine] = None
_engine_lock = threading.Lock()


def get_engine(
    lang: str = "es",
    volume: Optional[int] = None,
    cache_enabled: Optional[bool] = None,
    stream_sentences: Optional[bool] = None,
) -> AudioEngine:
    """Return (or create) the global AudioEngine singleton.

    Defaults are sourced from jarvis.config when not explicitly provided.
    """
    global _engine
    with _engine_lock:
        if _engine is None:
            try:
                from ..config import JARVIS_AUDIO_VOLUME, JARVIS_TTS_CACHE, JARVIS_TTS_STREAM
                cfg_vol = JARVIS_AUDIO_VOLUME
                cfg_cache = JARVIS_TTS_CACHE
                cfg_stream = JARVIS_TTS_STREAM
            except Exception:
                cfg_vol, cfg_cache, cfg_stream = 100, True, True

            _engine = AudioEngine(
                lang=lang,
                volume=volume if volume is not None else cfg_vol,
                cache_enabled=cache_enabled if cache_enabled is not None else cfg_cache,
                stream_sentences=stream_sentences if stream_sentences is not None else cfg_stream,
            )
        return _engine


def shutdown_engine() -> None:
    """Shutdown the global AudioEngine if it exists."""
    global _engine
    with _engine_lock:
        if _engine is not None:
            _engine.shutdown()
            _engine = None
