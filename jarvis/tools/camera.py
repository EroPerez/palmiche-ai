"""Camera vision: multimodal object & gesture recognition via the configured JARVIS_MODEL.

Captures frames from the system camera (OpenCV) and sends them to the
JarvisUniversalADKAgent's centralized LLM completion for analysis. This means
any multimodal-capable provider works: Gemini, Claude, GPT-4o, Ollama (gemma3,
llava), etc. — no separate vision model needed.

Features:
  - Single frame capture & describe
  - Object recognition
  - Hand gesture recognition
  - Continuous monitoring with callbacks

Install:
    pip install "palmiche-jarvis[vision]"
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

# cv2 bundles xcb but not dxcb; override before the first cv2 import so Qt
# doesn't abort trying to load a plugin that isn't there.
if os.environ.get("QT_QPA_PLATFORM") == "dxcb":
    os.environ["QT_QPA_PLATFORM"] = "xcb"


def _capture_frame(camera_index: int = 0, save_path: Optional[str] = None) -> tuple[bytes, str]:
    """Capture a single frame from the camera and return (jpeg_bytes, file_path).

    Raises ImportError if opencv-python is not installed.
    Raises RuntimeError if the camera cannot be opened.
    """
    try:
        import cv2
    except ImportError as exc:
        raise ImportError(
            "opencv-python no está instalado.\n"
            "Instala con: pip install opencv-python\n"
            f"Error: {exc}"
        ) from exc

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"No se pudo abrir la cámara (índice {camera_index}). "
            "Verifica que la cámara está conectada y no está en uso por otra aplicación."
        )

    try:
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError("No se pudo capturar un frame de la cámara.")

        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        jpeg_bytes = jpeg.tobytes()

        if save_path:
            dest = Path(save_path).expanduser()
        else:
            from datetime import datetime
            captures_dir = Path.home() / "Capturas"
            captures_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = captures_dir / f"camera_{ts}.jpg"

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(jpeg_bytes)

        return jpeg_bytes, str(dest)
    finally:
        cap.release()


_vision_agent = None


def _get_vision_agent():
    """Lazy singleton of JarvisUniversalADKAgent for vision tasks."""
    global _vision_agent
    if _vision_agent is None:
        from ..brain.adk_universal import JarvisUniversalADKAgent
        _vision_agent = JarvisUniversalADKAgent()
    return _vision_agent


def _analyze_image(image_bytes: bytes, prompt: str) -> str:
    """Send an image to JarvisUniversalADKAgent for multimodal analysis."""
    try:
        agent = _get_vision_agent()
        return agent.vision_chat(image_bytes, prompt)
    except Exception as e:
        return f"Error al analizar imagen: {e}"


def _get_camera_index() -> int:
    from ..config import VISION_CAMERA_INDEX
    return VISION_CAMERA_INDEX


def _try_show_frame(window_name: str, frame, wait_ms: int = 1) -> bool:
    """Try to display a frame via cv2.imshow. Returns False if GUI unavailable."""
    try:
        import cv2
        cv2.imshow(window_name, frame)
        cv2.waitKey(wait_ms)
        return True
    except Exception:
        return False


def _destroy_window(window_name: str) -> None:
    try:
        import cv2
        cv2.destroyWindow(window_name)
        cv2.waitKey(1)
    except Exception:
        pass


def _show_jpeg_preview(jpeg_bytes: bytes, window_name: str) -> None:
    """Decode JPEG bytes and show in a cv2 window (non-blocking)."""
    try:
        import cv2
        import numpy as np
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is not None:
            _try_show_frame(window_name, frame)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

_OBJECT_PROMPT = (
    "Analyze this image carefully. List every distinct object you can identify. "
    "For each object provide: name, approximate position in the frame "
    "(left/center/right, top/middle/bottom), estimated size relative to the frame, "
    "and confidence (high/medium/low). "
    "Format as a numbered list. Be thorough but precise."
)

_GESTURE_PROMPT = (
    "Analyze this image focusing on hand gestures and body language. "
    "Identify: 1) Number of hands visible, 2) Hand pose/gesture for each hand "
    "(e.g., open palm, fist, pointing, thumbs up, peace sign, OK sign, pinch, wave), "
    "3) Any body gestures or poses. "
    "Be specific about finger positions and hand orientation. "
    "If no hands or gestures are visible, say so clearly."
)

_DESCRIBE_PROMPT = (
    "Describe this image in detail. Include: the scene/setting, "
    "all visible objects and people, colors, lighting, and any notable details. "
    "Be thorough but concise."
)


def camera_capture(
    save_path: str = "",
    camera_index: int = -1,
    show_preview: bool = False,
) -> str:
    """Capture a photo from the camera and save it.

    Args:
        save_path: Where to save the image. Default: ~/Capturas/camera_TIMESTAMP.jpg
        camera_index: Camera device index (0=default). -1 uses config default.
        show_preview: Show the captured frame in a window.

    Returns:
        Path to the saved image file.
    """
    cam = camera_index if camera_index >= 0 else _get_camera_index()

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
        if show_preview:
            try:
                import cv2
                import numpy as np
                arr = np.frombuffer(image_bytes, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    _try_show_frame("Jarvis - Captura", frame, wait_ms=3000)
                    _destroy_window("Jarvis - Captura")
            except Exception:
                pass
        return f"Foto capturada y guardada en: {path}"
    except (ImportError, RuntimeError) as e:
        return str(e)


def camera_describe(
    prompt: str = "",
    camera_index: int = -1,
    save_path: str = "",
    show_preview: bool = False,
) -> str:
    """Capture a photo and describe what the camera sees using the configured AI model.

    Args:
        prompt: Custom prompt for the AI. Default: general scene description.
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to also save the captured image.
        show_preview: Show the captured frame in a preview window while analyzing.

    Returns:
        AI-generated description of the scene.
    """
    cam = camera_index if camera_index >= 0 else _get_camera_index()

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if show_preview:
        _show_jpeg_preview(image_bytes, "Jarvis - Describe")

    result = _analyze_image(image_bytes, prompt or _DESCRIBE_PROMPT)

    if show_preview:
        _destroy_window("Jarvis - Describe")

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_recognize_objects(
    camera_index: int = -1,
    save_path: str = "",
    show_preview: bool = False,
) -> str:
    """Capture a photo and identify all objects in the scene.

    Args:
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to save the captured image.
        show_preview: Show the captured frame in a preview window while analyzing.

    Returns:
        Structured list of detected objects.
    """
    cam = camera_index if camera_index >= 0 else _get_camera_index()

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if show_preview:
        _show_jpeg_preview(image_bytes, "Jarvis - Objetos")

    result = _analyze_image(image_bytes, _OBJECT_PROMPT)

    if show_preview:
        _destroy_window("Jarvis - Objetos")

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_recognize_gestures(
    camera_index: int = -1,
    save_path: str = "",
    show_preview: bool = False,
) -> str:
    """Capture a photo and recognize hand gestures and body language.

    Args:
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to save the captured image.
        show_preview: Show the captured frame in a preview window while analyzing.

    Returns:
        Description of detected gestures.
    """
    cam = camera_index if camera_index >= 0 else _get_camera_index()

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if show_preview:
        _show_jpeg_preview(image_bytes, "Jarvis - Gestos")

    result = _analyze_image(image_bytes, _GESTURE_PROMPT)

    if show_preview:
        _destroy_window("Jarvis - Gestos")

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_analyze(
    prompt: str,
    camera_index: int = -1,
    save_path: str = "",
    show_preview: bool = False,
) -> str:
    """Capture a photo and analyze it with a custom prompt.

    Flexible tool for any visual question: "How many people?",
    "What color is the shirt?", "Is the door open?", "Read the text on the sign", etc.

    Args:
        prompt: The question or instruction for the AI about the image.
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to save the captured image.
        show_preview: Show the captured frame in a preview window while analyzing.

    Returns:
        AI response to the visual prompt.
    """
    cam = camera_index if camera_index >= 0 else _get_camera_index()

    if not prompt:
        return "Error: Se requiere un prompt/pregunta para analizar la imagen."

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if show_preview:
        _show_jpeg_preview(image_bytes, "Jarvis - Análisis")

    result = _analyze_image(image_bytes, prompt)

    if show_preview:
        _destroy_window("Jarvis - Análisis")

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_monitor(
    task: str = "",
    duration: int = 10,
    interval: int = 3,
    camera_index: int = -1,
    show_preview: bool = False,
) -> str:
    """Monitor the camera for a period, analyzing frames at regular intervals.

    Args:
        task: What to monitor for (e.g., "count people", "detect movement",
              "watch for someone entering"). Default: general scene changes.
        duration: How many seconds to monitor (max 60). Default: 10.
        interval: Seconds between frame captures (min 2). Default: 3.
        camera_index: Camera device index. -1 uses config default.
        show_preview: Show a live preview window while monitoring.

    Returns:
        Summary of observations across all captured frames.
    """
    cam = camera_index if camera_index >= 0 else _get_camera_index()

    duration = max(1, min(duration, 60))
    interval = max(2, interval)

    monitor_prompt = (
        f"You are monitoring a camera feed. Your task: {task or 'describe any changes or activity'}. "
        "This is frame {frame_num} of {total_frames}. "
        "Be concise — focus only on what's relevant to the monitoring task. "
        "Note any changes from what you might expect in a static scene."
    )

    observations = []
    total_frames = max(1, (duration + interval - 1) // interval)
    start = time.time()
    next_capture_at = start
    preview_active = False
    window_name = "Jarvis - Monitor"

    try:
        import cv2
    except ImportError:
        return (
            "opencv-python no está instalado.\n"
            "Instala con: pip install opencv-python"
        )

    cap = cv2.VideoCapture(cam)
    if not cap.isOpened():
        return f"No se pudo abrir la cámara (índice {cam})."

    try:
        for _ in range(5):
            cap.read()

        frame_num = 0
        while frame_num < total_frames and next_capture_at - start < duration:
            sleep_for = next_capture_at - time.time()
            if sleep_for > 0:
                if show_preview and preview_active:
                    end_wait = time.time() + sleep_for
                    while time.time() < end_wait:
                        ret_p, frame_p = cap.read()
                        if ret_p and frame_p is not None:
                            _try_show_frame(window_name, frame_p, wait_ms=30)
                        else:
                            time.sleep(0.03)
                else:
                    time.sleep(sleep_for)

            frame_num += 1
            ret, frame = cap.read()
            if not ret or frame is None:
                observations.append(f"Frame {frame_num}: Error al capturar")
                next_capture_at = start + frame_num * interval
                continue

            if show_preview:
                preview_active = _try_show_frame(window_name, frame, wait_ms=1)

            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            image_bytes = jpeg.tobytes()

            current_prompt = monitor_prompt.format(
                frame_num=frame_num, total_frames=total_frames
            )

            result = _analyze_image(image_bytes, current_prompt)

            elapsed = time.time() - start
            observations.append(f"[{elapsed:.1f}s] Frame {frame_num}: {result}")

            next_capture_at = start + frame_num * interval
    finally:
        cap.release()
        if show_preview and preview_active:
            _destroy_window(window_name)

    header = f"Monitoreo de cámara ({duration}s, {frame_num} frames capturados)"
    if task:
        header += f"\nTarea: {task}"
    return header + "\n\n" + "\n\n".join(observations)


def camera_preview(
    duration: int = 15,
    camera_index: int = -1,
) -> str:
    """Open a live camera preview window. Shows what the camera sees in real time.

    The window stays open for the specified duration or until the user presses
    ESC or Q. No AI analysis is performed — this is purely for viewing.

    Args:
        duration: How many seconds to show the preview (max 120). Default: 15.
        camera_index: Camera device index. -1 uses config default.

    Returns:
        Status message about the preview session.
    """
    cam = camera_index if camera_index >= 0 else _get_camera_index()
    duration = max(1, min(duration, 120))
    window_name = "Jarvis - Preview (ESC para cerrar)"

    try:
        import cv2
    except ImportError:
        return (
            "opencv-python no está instalado.\n"
            "Instala con: pip install opencv-python"
        )

    cap = cv2.VideoCapture(cam)
    if not cap.isOpened():
        return f"No se pudo abrir la cámara (índice {cam})."

    try:
        for _ in range(5):
            cap.read()

        start = time.time()
        frames_shown = 0

        while time.time() - start < duration:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            if not _try_show_frame(window_name, frame, wait_ms=30):
                return "Error: No se pudo abrir la ventana de preview. Verifica que tienes un entorno gráfico disponible."

            frames_shown += 1

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q'), ord('Q')):
                elapsed = time.time() - start
                return f"Preview cerrado por el usuario después de {elapsed:.1f}s ({frames_shown} frames)."

        elapsed = time.time() - start
        return f"Preview completado: {elapsed:.1f}s, {frames_shown} frames mostrados."
    finally:
        cap.release()
        _destroy_window(window_name)
