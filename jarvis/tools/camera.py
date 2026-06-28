"""Camera vision: multimodal object & gesture recognition via Gemma 4 / Ollama.

Captures frames from the system camera (OpenCV) and sends them to a local
multimodal model (Gemma 4 12B by default) running on Ollama for analysis.

Features:
  - Single frame capture & describe
  - Object recognition
  - Hand gesture recognition
  - Continuous monitoring with callbacks

Backends for inference:
  ollama  – local Ollama server (default, no API key needed)
  gemini  – Google Gemini API (needs GOOGLE_API_KEY)

Install:
    pip install "palmiche-jarvis[vision]"
    ollama pull gemma3:4b   # or gemma3:12b for better quality
"""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path
from typing import Optional


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
            "Instala con: pip install opencv-python-headless\n"
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
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(jpeg_bytes)
            path_str = str(dest)
        else:
            from datetime import datetime
            captures_dir = Path.home() / "Capturas"
            captures_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = captures_dir / f"camera_{ts}.jpg"
            with open(dest, "wb") as f:
                f.write(jpeg_bytes)
            path_str = str(dest)

        return jpeg_bytes, path_str
    finally:
        cap.release()


def _analyze_with_ollama(
    image_bytes: bytes,
    prompt: str,
    model: str,
    host: str,
) -> str:
    """Send an image to Ollama's multimodal API and return the text response."""
    import requests

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    url = f"{host.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [b64_image],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 1024,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "No se recibió respuesta del modelo.")
    except requests.ConnectionError:
        return (
            f"Error: No se pudo conectar a Ollama en {host}. "
            "Verifica que Ollama está ejecutándose (ollama serve) y que el modelo está descargado "
            f"(ollama pull {model})."
        )
    except requests.Timeout:
        return "Error: Timeout al esperar respuesta de Ollama. El modelo puede estar cargándose."
    except Exception as e:
        return f"Error al comunicarse con Ollama: {e}"


def _analyze_with_gemini(
    image_bytes: bytes,
    prompt: str,
    model: str,
) -> str:
    """Send an image to Google Gemini API and return the text response."""
    from ..config import GOOGLE_API_KEY, JARVIS_API_KEY

    api_key = JARVIS_API_KEY or GOOGLE_API_KEY
    if not api_key:
        return (
            "Error: Se requiere GOOGLE_API_KEY o JARVIS_API_KEY para usar Gemini. "
            "Configúrala en jarvis/.env."
        )

    try:
        from google import genai
        from google.genai import types as gtypes
    except ImportError as exc:
        return (
            f"Error: google-genai no está instalado. "
            f"Instala con: pip install google-genai\nDetalle: {exc}"
        )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[
            gtypes.Content(
                role="user",
                parts=[
                    gtypes.Part(text=prompt),
                    gtypes.Part(
                        inline_data=gtypes.Blob(
                            mime_type="image/jpeg",
                            data=image_bytes,
                        )
                    ),
                ],
            )
        ],
        config=gtypes.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )

    if response.candidates and response.candidates[0].content:
        parts = response.candidates[0].content.parts
        return " ".join(p.text for p in parts if hasattr(p, "text") and p.text)

    return "No se recibió respuesta de Gemini."


def _get_vision_config():
    """Return resolved vision configuration values."""
    from ..config import (
        VISION_MODEL,
        VISION_BACKEND,
        VISION_OLLAMA_HOST,
        VISION_CAMERA_INDEX,
    )
    return VISION_MODEL, VISION_BACKEND, VISION_OLLAMA_HOST, VISION_CAMERA_INDEX


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
) -> str:
    """Capture a photo from the camera and save it.

    Args:
        save_path: Where to save the image. Default: ~/Capturas/camera_TIMESTAMP.jpg
        camera_index: Camera device index (0=default). -1 uses config default.

    Returns:
        Path to the saved image file.
    """
    _, _, _, default_cam = _get_vision_config()
    cam = camera_index if camera_index >= 0 else default_cam

    try:
        _, path = _capture_frame(cam, save_path or None)
        return f"Foto capturada y guardada en: {path}"
    except ImportError as e:
        return str(e)
    except RuntimeError as e:
        return str(e)


def camera_describe(
    prompt: str = "",
    camera_index: int = -1,
    save_path: str = "",
) -> str:
    """Capture a photo and describe what the camera sees using Gemma 4 multimodal AI.

    Args:
        prompt: Custom prompt for the AI. Default: general scene description.
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to also save the captured image.

    Returns:
        AI-generated description of the scene.
    """
    model, backend, host, default_cam = _get_vision_config()
    cam = camera_index if camera_index >= 0 else default_cam
    analysis_prompt = prompt or _DESCRIBE_PROMPT

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if backend == "gemini":
        result = _analyze_with_gemini(image_bytes, analysis_prompt, model)
    else:
        result = _analyze_with_ollama(image_bytes, analysis_prompt, model, host)

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_recognize_objects(
    camera_index: int = -1,
    save_path: str = "",
) -> str:
    """Capture a photo and identify all objects in the scene.

    Uses Gemma 4 multimodal AI to detect and list objects with positions
    and confidence levels.

    Args:
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to save the captured image.

    Returns:
        Structured list of detected objects.
    """
    model, backend, host, default_cam = _get_vision_config()
    cam = camera_index if camera_index >= 0 else default_cam

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if backend == "gemini":
        result = _analyze_with_gemini(image_bytes, _OBJECT_PROMPT, model)
    else:
        result = _analyze_with_ollama(image_bytes, _OBJECT_PROMPT, model, host)

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_recognize_gestures(
    camera_index: int = -1,
    save_path: str = "",
) -> str:
    """Capture a photo and recognize hand gestures and body language.

    Uses Gemma 4 multimodal AI to detect hand poses, finger positions,
    and gestures (thumbs up, peace, pointing, fist, open palm, etc.).

    Args:
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to save the captured image.

    Returns:
        Description of detected gestures.
    """
    model, backend, host, default_cam = _get_vision_config()
    cam = camera_index if camera_index >= 0 else default_cam

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if backend == "gemini":
        result = _analyze_with_gemini(image_bytes, _GESTURE_PROMPT, model)
    else:
        result = _analyze_with_ollama(image_bytes, _GESTURE_PROMPT, model, host)

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_analyze(
    prompt: str,
    camera_index: int = -1,
    save_path: str = "",
) -> str:
    """Capture a photo and analyze it with a custom prompt.

    Flexible tool for any visual question: "How many people?",
    "What color is the shirt?", "Is the door open?", "Read the text on the sign", etc.

    Args:
        prompt: The question or instruction for the AI about the image.
        camera_index: Camera device index. -1 uses config default.
        save_path: Optional path to save the captured image.

    Returns:
        AI response to the visual prompt.
    """
    model, backend, host, default_cam = _get_vision_config()
    cam = camera_index if camera_index >= 0 else default_cam

    if not prompt:
        return "Error: Se requiere un prompt/pregunta para analizar la imagen."

    try:
        image_bytes, path = _capture_frame(cam, save_path or None)
    except (ImportError, RuntimeError) as e:
        return str(e)

    if backend == "gemini":
        result = _analyze_with_gemini(image_bytes, prompt, model)
    else:
        result = _analyze_with_ollama(image_bytes, prompt, model, host)

    return f"[Imagen guardada: {path}]\n\n{result}"


def camera_monitor(
    task: str = "",
    duration: int = 10,
    interval: int = 3,
    camera_index: int = -1,
) -> str:
    """Monitor the camera for a period, analyzing frames at regular intervals.

    Useful for detecting changes, counting people over time, monitoring
    activity, or watching for specific events.

    Args:
        task: What to monitor for (e.g., "count people", "detect movement",
              "watch for someone entering"). Default: general scene changes.
        duration: How many seconds to monitor (max 60). Default: 10.
        interval: Seconds between frame captures (min 2). Default: 3.
        camera_index: Camera device index. -1 uses config default.

    Returns:
        Summary of observations across all captured frames.
    """
    model, backend, host, default_cam = _get_vision_config()
    cam = camera_index if camera_index >= 0 else default_cam

    duration = max(1, min(duration, 60))
    interval = max(2, interval)

    monitor_prompt = (
        f"You are monitoring a camera feed. Your task: {task or 'describe any changes or activity'}. "
        "This is frame {frame_num} of {total_frames}. "
        "Be concise — focus only on what's relevant to the monitoring task. "
        "Note any changes from what you might expect in a static scene."
    )

    observations = []
    total_frames = max(1, duration // interval)
    start = time.time()

    try:
        import cv2
    except ImportError as e:
        return str(ImportError(
            "opencv-python no está instalado.\n"
            "Instala con: pip install opencv-python-headless"
        ))

    cap = cv2.VideoCapture(cam)
    if not cap.isOpened():
        return f"No se pudo abrir la cámara (índice {cam})."

    try:
        for _ in range(5):
            cap.read()

        frame_num = 0
        while time.time() - start < duration and frame_num < total_frames:
            frame_num += 1
            ret, frame = cap.read()
            if not ret or frame is None:
                observations.append(f"Frame {frame_num}: Error al capturar")
                continue

            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            image_bytes = jpeg.tobytes()

            current_prompt = monitor_prompt.format(
                frame_num=frame_num, total_frames=total_frames
            )

            if backend == "gemini":
                result = _analyze_with_gemini(image_bytes, current_prompt, model)
            else:
                result = _analyze_with_ollama(image_bytes, current_prompt, model, host)

            elapsed = time.time() - start
            observations.append(f"[{elapsed:.1f}s] Frame {frame_num}: {result}")

            if frame_num < total_frames:
                time.sleep(interval)
    finally:
        cap.release()

    header = f"Monitoreo de cámara ({duration}s, {frame_num} frames capturados)"
    if task:
        header += f"\nTarea: {task}"
    return header + "\n\n" + "\n\n".join(observations)
