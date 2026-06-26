"""Centralized audio engine for Jarvis.

Provides a queue-based audio playback system with TTS caching, volume control,
sentence-level streaming, and interrupt support. Replaces direct subprocess
calls scattered across wake_word.py and voice.py with a unified interface.

Requires: pip install SpeechRecognition pyaudio gtts pyttsx3
"""

import hashlib
import logging
import os
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

_TTS_CACHE_DIR = Path(tempfile.gettempdir()) / "jarvis_tts_cache"

# Sentence boundary regex — splits on period, exclamation, question mark, or
# semicolon followed by whitespace (keeps short clauses together).
_SENTENCE_RE = re.compile(r"(?<=[.!?;])\s+")

# Maximum cached TTS files before eviction (LRU by mtime).
_MAX_CACHE_FILES = 200


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
    ):
        self.lang = lang
        self._volume = max(0, min(100, volume))
        self._cache_enabled = cache_enabled
        self._stream_sentences = stream_sentences

        self._queue: list[tuple[str, dict]] = []
        self._queue_lock = threading.Lock()
        self._queue_event = threading.Event()
        self._current_process: Optional[subprocess.Popen] = None
        self._process_lock = threading.Lock()
        self._stopped = threading.Event()
        self._shutdown = threading.Event()

        self._worker = threading.Thread(
            target=self._playback_worker, daemon=True, name="jarvis-audio-engine"
        )
        self._worker.start()

        if cache_enabled:
            _TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ public

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, value: int):
        self._volume = max(0, min(100, value))

    def speak(self, text: str, block: bool = False) -> None:
        """Enqueue text for TTS playback.

        If *stream_sentences* is enabled, long text is split at sentence
        boundaries so the first sentence starts playing while the rest are
        still being synthesised.
        """
        from .wake_word import _clean_for_tts

        text = _clean_for_tts(text)
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

    def play_file(self, path: str, block: bool = False) -> None:
        """Enqueue an audio file for playback."""
        if not os.path.isfile(path):
            logger.warning("Audio file not found: %s", path)
            return
        self._enqueue("file", {"path": path})
        if block:
            self.wait()

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
        self._shutdown.set()
        self._queue_event.set()

    def is_idle(self) -> bool:
        """Return True if nothing is playing and the queue is empty."""
        with self._queue_lock:
            return len(self._queue) == 0 and not self._is_playing()

    # ---------------------------------------------------- TTS cache management

    def clear_cache(self) -> int:
        """Remove all cached TTS files. Returns number of files deleted."""
        count = 0
        if _TTS_CACHE_DIR.exists():
            for f in _TTS_CACHE_DIR.iterdir():
                try:
                    f.unlink()
                    count += 1
                except OSError:
                    pass
        return count

    def cache_stats(self) -> dict:
        """Return cache statistics: file count and total size in bytes."""
        if not _TTS_CACHE_DIR.exists():
            return {"files": 0, "size_bytes": 0}
        files = list(_TTS_CACHE_DIR.iterdir())
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
        while not self._shutdown.is_set():
            self._queue_event.wait(timeout=0.5)
            self._queue_event.clear()
            self._stopped.clear()

            while not self._shutdown.is_set():
                item = self._dequeue()
                if item is None:
                    break
                if self._stopped.is_set():
                    break

                kind, data = item
                try:
                    if kind == "tts":
                        self._play_tts(data["text"])
                    elif kind == "file":
                        self._play_file_internal(data["path"])
                except Exception as exc:
                    logger.debug("Audio playback error: %s", exc)

    # ------------------------------------------------------------- TTS helpers

    def _cache_key(self, text: str) -> str:
        raw = f"{text}|{self.lang}".encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def _get_cached(self, text: str) -> Optional[str]:
        if not self._cache_enabled:
            return None
        key = self._cache_key(text)
        path = _TTS_CACHE_DIR / f"{key}.mp3"
        if path.is_file():
            path.touch()
            return str(path)
        return None

    def _put_cache(self, text: str, mp3_path: str) -> str:
        if not self._cache_enabled:
            return mp3_path
        key = self._cache_key(text)
        dest = _TTS_CACHE_DIR / f"{key}.mp3"
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
                _TTS_CACHE_DIR.iterdir(), key=lambda f: f.stat().st_mtime
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
            self._put_cache(text, mp3)
            self._play_file_internal(mp3)
            try:
                if not self._cache_enabled:
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
        import platform

        system = platform.system()
        try:
            if system == "Linux":
                amp = str(max(1, int(200 * self._volume / 100)))
                subprocess.run(
                    ["espeak-ng", "-v", "es", "-s", "130", "-p", "40", "-a", amp, text],
                    check=False,
                    capture_output=True,
                )
            elif system == "Darwin":
                subprocess.run(["say", "-v", "Monica", text], check=False)
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

        vol_ffplay = str(vol_pct / 100.0)
        candidates.append([
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            "-volume", vol_ffplay, path,
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
            return self._current_process is not None and self._current_process.poll() is None


# ---------------------------------------------------------------------------
# Module-level singleton for easy access
# ---------------------------------------------------------------------------

_engine: Optional[AudioEngine] = None
_engine_lock = threading.Lock()


def get_engine(
    lang: str = "es",
    volume: int = 100,
    cache_enabled: bool = True,
    stream_sentences: bool = True,
) -> AudioEngine:
    """Return (or create) the global AudioEngine singleton."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = AudioEngine(
                lang=lang,
                volume=volume,
                cache_enabled=cache_enabled,
                stream_sentences=stream_sentences,
            )
        return _engine


def shutdown_engine() -> None:
    """Shutdown the global AudioEngine if it exists."""
    global _engine
    with _engine_lock:
        if _engine is not None:
            _engine.shutdown()
            _engine = None
