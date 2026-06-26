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
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jarvis.interface.audio_engine import AudioEngine, _SENTENCE_RE


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
    engine = AudioEngine(volume=150)
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
    engine = AudioEngine()
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
    engine = AudioEngine()
    k1 = engine._cache_key("hola")
    k2 = engine._cache_key("hola")
    assert k1 == k2
    k3 = engine._cache_key("adiós")
    assert k1 != k3
    engine.shutdown()


def test_cache_key_lang_sensitive():
    engine_es = AudioEngine(lang="es")
    engine_en = AudioEngine(lang="en")
    assert engine_es._cache_key("hello") != engine_en._cache_key("hello")
    engine_es.shutdown()
    engine_en.shutdown()


# ---------------------------------------------------------------------------
# Cache put/get round-trip
# ---------------------------------------------------------------------------


def test_cache_round_trip():
    engine = AudioEngine(cache_enabled=True)
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
    engine = AudioEngine(cache_enabled=False)
    assert engine._get_cached("anything") is None
    engine.shutdown()


# ---------------------------------------------------------------------------
# Cache stats
# ---------------------------------------------------------------------------


def test_cache_stats():
    engine = AudioEngine(cache_enabled=True)
    engine.clear_cache()
    stats = engine.cache_stats()
    assert stats["files"] == 0
    engine.shutdown()


# ---------------------------------------------------------------------------
# is_idle
# ---------------------------------------------------------------------------


def test_is_idle_initial():
    engine = AudioEngine()
    assert engine.is_idle()
    engine.shutdown()


# ---------------------------------------------------------------------------
# play_file with missing file
# ---------------------------------------------------------------------------


def test_play_file_missing_logs_warning():
    engine = AudioEngine()
    with patch("jarvis.interface.audio_engine.logger") as mock_log:
        engine.play_file("/nonexistent/file.mp3")
        mock_log.warning.assert_called_once()
    engine.shutdown()


# ---------------------------------------------------------------------------
# speak with empty text
# ---------------------------------------------------------------------------


def test_speak_empty():
    engine = AudioEngine()
    engine.speak("")
    time.sleep(0.1)
    assert engine.is_idle()
    engine.shutdown()


# ---------------------------------------------------------------------------
# Streaming: long text gets split
# ---------------------------------------------------------------------------


def test_stream_sentences_enqueues_multiple():
    engine = AudioEngine(stream_sentences=True)
    long_text = "Primera oración larga que supera el límite. Segunda oración también larga para probar. Tercera oración para completar el test."
    engine.stop()  # prevent actual playback

    with patch.object(engine, "_enqueue") as mock_enq:
        engine.speak(long_text)
        assert mock_enq.call_count == 3

    engine.shutdown()


def test_stream_disabled_single_enqueue():
    engine = AudioEngine(stream_sentences=False)
    long_text = "Primera oración. Segunda oración. Tercera oración que es mucho más larga para superar el límite de caracteres establecido."

    with patch.object(engine, "_enqueue") as mock_enq:
        engine.speak(long_text)
        assert mock_enq.call_count == 1

    engine.shutdown()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

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
