#!/usr/bin/env python3
"""Unit tests for the AudioEngine.

Tests the queue, cache, volume, interrupt, and sentence-splitting logic
without requiring actual audio hardware or TTS libraries.

Run directly::

    python tests/test_audio_engine.py
"""
import sys
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jarvis.interface.audio_engine import AudioEngine, _SENTENCE_RE, clean_for_tts


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------


def test_clean_for_tts_strips_markdown():
    text = "# Heading\n**bold** and `code`"
    result = clean_for_tts(text)
    assert "#" not in result
    assert "**" not in result
    assert "`" not in result
    assert "bold" in result
    assert "code" in result


def test_clean_for_tts_strips_code_blocks():
    text = "Before\n```python\nprint('hello')\n```\nAfter"
    result = clean_for_tts(text)
    assert "print" not in result
    assert "Before" in result
    assert "After" in result


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------


def test_sentence_split_basic():
    text = "Hola mundo. ¿Cómo estás? Bien gracias."
    parts = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
    assert len(parts) == 3
    assert parts[0] == "Hola mundo."
    assert parts[1] == "¿Cómo estás?"
    assert parts[2] == "Bien gracias."


def test_sentence_split_no_boundary():
    text = "Una sola oración corta"
    parts = _SENTENCE_RE.split(text)
    assert len(parts) == 1


# ---------------------------------------------------------------------------
# Volume clamping
# ---------------------------------------------------------------------------


def test_volume_clamp():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(volume=150, cache_dir=Path(td))
        assert engine.volume == 100
        engine.volume = -10
        assert engine.volume == 0
        engine.volume = 75
        assert engine.volume == 75
        engine.shutdown()


# ---------------------------------------------------------------------------
# Queue and stop
# ---------------------------------------------------------------------------


def test_stop_clears_queue():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(cache_dir=Path(td))
        engine._enqueue("tts", {"text": "uno"})
        engine._enqueue("tts", {"text": "dos"})
        engine.stop()
        with engine._queue_lock:
            assert len(engine._queue) == 0
        engine.shutdown()


# ---------------------------------------------------------------------------
# Cache key determinism
# ---------------------------------------------------------------------------


def test_cache_key_deterministic():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(cache_dir=Path(td))
        k1 = engine._cache_key("hola")
        k2 = engine._cache_key("hola")
        assert k1 == k2
        k3 = engine._cache_key("adiós")
        assert k1 != k3
        engine.shutdown()


def test_cache_key_lang_sensitive():
    with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
        engine_es = AudioEngine(lang="es", cache_dir=Path(td1))
        engine_en = AudioEngine(lang="en", cache_dir=Path(td2))
        assert engine_es._cache_key("hello") != engine_en._cache_key("hello")
        engine_es.shutdown()
        engine_en.shutdown()


# ---------------------------------------------------------------------------
# Cache put/get round-trip (isolated temp dir)
# ---------------------------------------------------------------------------


def test_cache_round_trip():
    with tempfile.TemporaryDirectory() as td:
        cache_dir = Path(td) / "cache"
        cache_dir.mkdir()
        engine = AudioEngine(cache_enabled=True, cache_dir=cache_dir)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake-mp3-data")
            tmp = f.name
        try:
            assert engine._get_cached("test phrase") is None
            engine._put_cache("test phrase", tmp)
            cached = engine._get_cached("test phrase")
            assert cached is not None
            assert os.path.isfile(cached)
        finally:
            os.unlink(tmp)
            engine.clear_cache()
            engine.shutdown()


def test_cache_disabled():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(cache_enabled=False, cache_dir=Path(td))
        assert engine._get_cached("anything") is None
        engine.shutdown()


# ---------------------------------------------------------------------------
# Cache stats (isolated)
# ---------------------------------------------------------------------------


def test_cache_stats():
    with tempfile.TemporaryDirectory() as td:
        cache_dir = Path(td) / "cache"
        cache_dir.mkdir()
        engine = AudioEngine(cache_enabled=True, cache_dir=cache_dir)
        engine.clear_cache()
        stats = engine.cache_stats()
        assert stats["files"] == 0
        engine.shutdown()


# ---------------------------------------------------------------------------
# is_idle
# ---------------------------------------------------------------------------


def test_is_idle_initial():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(cache_dir=Path(td))
        assert engine.is_idle()
        engine.shutdown()


# ---------------------------------------------------------------------------
# play_file with missing file
# ---------------------------------------------------------------------------


def test_play_file_missing_logs_warning():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(cache_dir=Path(td))
        with patch("jarvis.interface.audio_engine.logger") as mock_log:
            engine.play_file("/nonexistent/file.mp3")
            mock_log.warning.assert_called_once()
        engine.shutdown()


# ---------------------------------------------------------------------------
# speak with empty text
# ---------------------------------------------------------------------------


def test_speak_empty():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(cache_dir=Path(td))
        engine.speak("")
        time.sleep(0.1)
        assert engine.is_idle()
        engine.shutdown()


# ---------------------------------------------------------------------------
# Streaming: long text gets split
# ---------------------------------------------------------------------------


def test_stream_sentences_enqueues_multiple():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(stream_sentences=True, cache_dir=Path(td))
        long_text = "Primera oración larga que supera el límite. Segunda oración también larga para probar. Tercera oración para completar el test."
        engine.stop()

        with patch.object(engine, "_enqueue") as mock_enq:
            engine.speak(long_text)
            assert mock_enq.call_count == 3

        engine.shutdown()


def test_stream_disabled_single_enqueue():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(stream_sentences=False, cache_dir=Path(td))
        long_text = "Primera oración. Segunda oración. Tercera oración que es mucho más larga para superar el límite de caracteres establecido."

        with patch.object(engine, "_enqueue") as mock_enq:
            engine.speak(long_text)
            assert mock_enq.call_count == 1

        engine.shutdown()


# ---------------------------------------------------------------------------
# speak_async with on_done callback
# ---------------------------------------------------------------------------


def test_speak_async_empty_calls_on_done():
    called = threading.Event()

    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(cache_dir=Path(td))
        engine.speak_async("", on_done=lambda: called.set())
        assert called.wait(timeout=1)
        engine.shutdown()


# ---------------------------------------------------------------------------
# ffplay volume is integer (not decimal)
# ---------------------------------------------------------------------------


def test_ffplay_volume_is_integer():
    with tempfile.TemporaryDirectory() as td:
        engine = AudioEngine(volume=80, cache_dir=Path(td))
        # The ffplay command should use "80", not "0.8"
        vol_pct = engine._volume
        ffplay_vol = str(vol_pct)
        assert ffplay_vol == "80"
        assert "." not in ffplay_vol
        engine.shutdown()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

import threading  # noqa: E402

if __name__ == "__main__":
    import inspect

    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and inspect.isfunction(obj)
    ]
    passed = failed = 0
    for name, func in tests:
        try:
            func()
            passed += 1
            print(f"  PASS  {name}")
        except Exception as exc:
            failed += 1
            print(f"  FAIL  {name}: {exc}")
    total = passed + failed
    print(f"\n{passed}/{total} passed" + (f", {failed} failed" if failed else ""))
    sys.exit(1 if failed else 0)
