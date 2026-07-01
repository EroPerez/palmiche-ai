"""A2A client — connects to remote A2A-compatible agents and wraps them as local tools.

Usage example (from Python):
    from jarvis.a2a.client import A2AClient
    client = A2AClient("http://agent2:8080")
    response = client.send_task("What is the weather today?")

Integration with DynamicToolRegistry:
    from jarvis.a2a.client import load_a2a_agent
    from jarvis.tools.dynamic import DynamicToolRegistry
    registry = DynamicToolRegistry()
    load_a2a_agent(registry, "http://agent2:8080")
"""
from __future__ import annotations

import sys
import uuid
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from .models import AgentCapabilities, AgentCard, AgentSkill


class A2AClient:
    """Synchronous HTTP client for A2A agents."""

    def __init__(self, base_url: str, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session_id: str = str(uuid.uuid4())
        self._card: Optional[AgentCard] = None

    def _http(self):
        if requests is None:
            raise ImportError("'requests' no está instalado. Instálalo con: pip install requests")
        return requests

    def get_agent_card(self) -> AgentCard:
        """Fetch and cache the remote agent's card."""
        if self._card is not None:
            return self._card
        resp = self._http().get(
            f"{self.base_url}/.well-known/agent.json",
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        capabilities = AgentCapabilities(
            **{
                k: data.get("capabilities", {}).get(k, v)
                for k, v in AgentCapabilities().__dict__.items()
            }
        )
        skills = [
            AgentSkill(
                id=s.get("id", ""),
                name=s.get("name", ""),
                description=s.get("description", ""),
                tags=s.get("tags", []),
            )
            for s in data.get("skills", [])
        ]
        self._card = AgentCard(
            name=data.get("name", "Remote Agent"),
            description=data.get("description", ""),
            url=data.get("url", self.base_url),
            version=data.get("version", "1.0.0"),
            capabilities=capabilities,
            skills=skills,
            defaultInputModes=data.get("defaultInputModes", ["text"]),
            defaultOutputModes=data.get("defaultOutputModes", ["text"]),
        )
        return self._card

    def send_task(self, message: str, session_id: Optional[str] = None) -> str:
        """Send a task to the remote agent and return the text response."""
        sid = session_id or self._session_id
        task_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "id": task_id,
                "sessionId": sid,
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": message}],
                },
            },
            "id": 1,
        }
        resp = self._http().post(
            self.base_url,
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(data["error"].get("message", "Unknown A2A error"))

        result = data.get("result", {})
        # Extract text from the first artifact
        for artifact in result.get("artifacts", []):
            for part in artifact.get("parts", []):
                if part.get("type") == "text":
                    return part.get("text", "")

        # Fallback: check status message
        status_msg = result.get("status", {}).get("message", {})
        if status_msg:
            for part in status_msg.get("parts", []):
                if part.get("type") == "text":
                    return part.get("text", "")

        return ""


def load_a2a_agent(registry, url: str, tool_name_prefix: str = "") -> str:
    """Discover an A2A agent and register it as a tool in the given DynamicToolRegistry.

    Returns the registered tool name.
    """
    client = A2AClient(url)
    try:
        card = client.get_agent_card()
        agent_name = card.name
        agent_description = card.description
    except Exception as exc:
        print(
            f"  [A2A] Advertencia: no se pudo obtener el agent card de {url}: {exc}",
            file=sys.stderr,
        )
        agent_name = url.split("//")[-1].replace(":", "_").replace("/", "_")
        agent_description = f"Agente A2A remoto en {url}"

    # Sanitize name for use as tool identifier
    safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in agent_name.lower())
    tool_name = f"{tool_name_prefix}delegate_to_{safe_name}" if tool_name_prefix else f"delegate_to_{safe_name}"

    definition = {
        "name": tool_name,
        "description": (
            f"Delega una tarea al agente remoto '{agent_name}' ({url}). "
            f"{agent_description}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensaje o tarea a enviar al agente remoto",
                }
            },
            "required": ["message"],
        },
    }

    def _handler(inputs: dict) -> str:
        return client.send_task(inputs.get("message", ""))

    registry.register(definition, _handler)
    return tool_name
