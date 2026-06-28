"""Centralized LLM completion — shared by tools that need direct model calls.

Uses the same model resolution, API key handling, and base URL configuration
as JarvisUniversalADKAgent so all LLM calls go through a single codepath.
"""
from __future__ import annotations

from ..config import JARVIS_API_KEY, JARVIS_BASE_URL, JARVIS_MODEL


def _ollama_completion(messages: list[dict], model: str, host: str, **kwargs) -> str:
    """Call the Ollama REST API directly for multimodal inference."""
    import requests

    ollama_model = model.split("/", 1)[1]
    url = f"{host.rstrip('/')}/api/generate"

    prompt_parts = []
    images = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            prompt_parts.append(content)
        elif isinstance(content, list):
            for part in content:
                if part.get("type") == "text":
                    prompt_parts.append(part["text"])
                elif part.get("type") == "image_url":
                    data_url = part["image_url"]["url"]
                    if data_url.startswith("data:"):
                        b64 = data_url.split(",", 1)[1]
                        images.append(b64)

    payload = {
        "model": ollama_model,
        "prompt": "\n".join(prompt_parts),
        "stream": False,
        "options": {
            "temperature": kwargs.get("temperature", 0.3),
            "num_predict": kwargs.get("max_tokens", 1024),
        },
    }
    if images:
        payload["images"] = images

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "No se recibió respuesta del modelo.")
    except requests.ConnectionError:
        return (
            f"Error: No se pudo conectar a Ollama en {host}. "
            "Verifica que Ollama está ejecutándose (ollama serve) y que el modelo está descargado "
            f"(ollama pull {ollama_model})."
        )
    except requests.Timeout:
        return "Error: Timeout al esperar respuesta de Ollama. El modelo puede estar cargándose."
    except Exception as e:
        return f"Error al comunicarse con Ollama: {e}"


def completion(messages: list[dict], **kwargs) -> str:
    """Run a one-shot LLM completion using the same config as JarvisUniversalADKAgent.

    Args:
        messages: OpenAI-format messages (supports multimodal content blocks).
        **kwargs: Extra params forwarded to litellm.completion (temperature, max_tokens, etc.).

    Returns:
        The model's text response, or an error string on failure.
    """
    from .adk_universal import _normalize_model_str

    model = _normalize_model_str(JARVIS_MODEL)

    if model.startswith(("ollama_chat/", "ollama/")):
        return _ollama_completion(
            messages, model,
            host=JARVIS_BASE_URL or "http://localhost:11434",
            **kwargs,
        )

    try:
        import litellm
    except ImportError as exc:
        return (
            "Error: litellm no está instalado.\n"
            f"Instala con: pip install litellm\nDetalle: {exc}"
        )

    call_kwargs: dict = {"model": model, "messages": messages, **kwargs}
    if JARVIS_API_KEY:
        call_kwargs["api_key"] = JARVIS_API_KEY
    if JARVIS_BASE_URL:
        call_kwargs["api_base"] = JARVIS_BASE_URL

    try:
        response = litellm.completion(**call_kwargs)
        return response.choices[0].message.content or "No se recibió respuesta del modelo."
    except Exception as e:
        return f"Error al completar con {model}: {e}"
