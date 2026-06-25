import anthropic
from ..config import ANTHROPIC_API_KEY, JARVIS_MODEL, JARVIS_NAME
from .prompts import SYSTEM_PROMPT
from ..tools.registry import TOOL_DEFINITIONS, execute_tool
from ..memory.history import ConversationHistory


class JarvisAgent:
    """Jarvis agent powered by the Anthropic SDK with a manual tool-use loop."""

    def __init__(self, name: str = JARVIS_NAME, registry=None):
        """Initialize the Anthropic client and load conversation history.

        Args:
            name: Display name for the assistant.
            registry: Optional DynamicToolRegistry. When provided, its tools and executor
                      are used instead of the static TOOL_DEFINITIONS / execute_tool.
                      This enables MCP and A2A client tools at runtime.
        """
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.history = ConversationHistory()
        self.system_prompt = SYSTEM_PROMPT.format(name=name)
        self._registry = registry

    def _tool_definitions(self) -> list:
        return self._registry.definitions if self._registry is not None else TOOL_DEFINITIONS

    def _execute_tool(self, name: str, inputs: dict) -> str:
        if self._registry is not None:
            return self._registry.execute(name, inputs)
        return str(execute_tool(name, inputs))

    def chat(self, user_message: str) -> str:
        """Send a user message and run the agentic loop until end_turn or 10 iterations."""
        self.history.add("user", user_message)
        messages = self.history.get_messages()

        for _ in range(10):  # safety limit on tool use loops
            try:
                response = self.client.messages.create(
                    model=JARVIS_MODEL,
                    max_tokens=4096,
                    system=self.system_prompt,
                    tools=self._tool_definitions(),
                    messages=messages,
                )
            except Exception as exc:
                error_msg = f"Error al consultar el modelo: {exc}"
                self.history.add("assistant", error_msg)
                return error_msg

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result),
                            }
                        )

                messages.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                text = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                self.history.add("assistant", text)
                return text

            else:
                msg = f"Respuesta inesperada: {response.stop_reason}"
                self.history.add("assistant", msg)
                return msg

        msg = "Se alcanzó el límite de iteraciones de herramientas."
        self.history.add("assistant", msg)
        return msg
