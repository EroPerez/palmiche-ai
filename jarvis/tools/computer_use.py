"""Computer use: Gemini-powered visual browser/desktop automation.

Palmiche-AI gains the ability to control a browser or the full desktop by:
  1. Taking a screenshot of the current state
  2. Sending it to Gemini with computer-use capability
  3. Executing Gemini's actions (click, type, scroll, navigate, key press…)
  4. Repeating until the task is complete

Backends:
  playwright  – Chromium browser via Playwright (pip install playwright)
  desktop     – Full desktop via pyautogui + mss/Pillow (pip install pyautogui mss)

Install:
    pip install "palmiche-jarvis[computer-use]"
    playwright install chromium   # only for playwright backend
"""
from __future__ import annotations

import base64
import io
import os
import time
from dataclasses import dataclass
from typing import Any, Literal, Optional

# ---------------------------------------------------------------------------
# Shared state container
# ---------------------------------------------------------------------------


@dataclass
class _EnvState:
    """Current environment state: PNG screenshot bytes + active URL."""
    screenshot: bytes
    url: str = ""


# ---------------------------------------------------------------------------
# Computer backends
# ---------------------------------------------------------------------------


class _PlaywrightComputer:
    """Browser-level computer controlled via Playwright (Chromium)."""

    SCREEN_WIDTH = 1440
    SCREEN_HEIGHT = 900

    def __init__(self, initial_url: str = "https://www.google.com", headless: bool = True):
        """Launch Chromium via Playwright and open *initial_url*."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ImportError(
                "Playwright no está instalado.\n"
                "Instala con: pip install playwright && playwright install chromium\n"
                f"Error: {exc}"
            ) from exc

        self._initial_url = initial_url
        self._headless = headless
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = self._browser.new_context(
            viewport={"width": self.SCREEN_WIDTH, "height": self.SCREEN_HEIGHT}
        )
        self._page = ctx.new_page()
        if initial_url:
            self._page.goto(initial_url)

    def close(self):
        """Close the browser and stop Playwright."""
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass

    def screen_size(self) -> tuple[int, int]:
        """Return the viewport dimensions as (width, height)."""
        return self.SCREEN_WIDTH, self.SCREEN_HEIGHT

    def _state(self) -> _EnvState:
        """Capture the current page screenshot and URL as an EnvState."""
        png = self._page.screenshot(full_page=False)
        return _EnvState(screenshot=png, url=self._page.url)

    # --- Navigation ---

    def navigate(self, url: str) -> _EnvState:
        """Navigate to *url* and return the new page state."""
        self._page.goto(url)
        return self._state()

    def go_back(self) -> _EnvState:
        """Navigate back in browser history."""
        self._page.go_back()
        return self._state()

    def go_forward(self) -> _EnvState:
        """Navigate forward in browser history."""
        self._page.go_forward()
        return self._state()

    def open_web_browser(self) -> _EnvState:
        """Return the current page state (browser is already open)."""
        return self._state()

    def search(self) -> _EnvState:
        """Focus the browser address bar via Ctrl+L."""
        self._page.keyboard.press("Control+l")
        return self._state()

    # --- Mouse ---

    def click_at(self, x: int, y: int) -> _EnvState:
        """Left-click at pixel coordinates (x, y)."""
        self._page.mouse.click(x, y)
        return self._state()

    def double_click_at(self, x: int, y: int) -> _EnvState:
        """Double-click at pixel coordinates (x, y)."""
        self._page.mouse.dblclick(x, y)
        return self._state()

    def triple_click_at(self, x: int, y: int) -> _EnvState:
        """Triple-click (select all text) at pixel coordinates (x, y)."""
        self._page.mouse.click(x, y, click_count=3)
        return self._state()

    def middle_click_at(self, x: int, y: int) -> _EnvState:
        """Middle-click at (x, y) to open links in a new tab."""
        self._page.mouse.click(x, y, button="middle")
        return self._state()

    def right_click_at(self, x: int, y: int) -> _EnvState:
        """Right-click at (x, y) to open the context menu."""
        self._page.mouse.click(x, y, button="right")
        return self._state()

    def hover_at(self, x: int, y: int) -> _EnvState:
        """Move the mouse pointer to (x, y) without clicking."""
        self._page.mouse.move(x, y)
        return self._state()

    def mouse_down(self, x: int, y: int) -> _EnvState:
        """Move to (x, y) and press the left mouse button down."""
        self._page.mouse.move(x, y)
        self._page.mouse.down()
        return self._state()

    def mouse_up(self, x: int, y: int) -> _EnvState:
        """Move to (x, y) and release the left mouse button."""
        self._page.mouse.move(x, y)
        self._page.mouse.up()
        return self._state()

    def drag_and_drop(self, x: int, y: int, destination_x: int, destination_y: int) -> _EnvState:
        """Drag from (x, y) and drop at (destination_x, destination_y)."""
        self._page.mouse.move(x, y)
        self._page.mouse.down()
        self._page.mouse.move(destination_x, destination_y)
        self._page.mouse.up()
        return self._state()

    # --- Keyboard ---

    def type_text(self, text: str, press_enter: bool = False) -> _EnvState:
        """Type *text* into the focused element, optionally pressing Enter."""
        self._page.keyboard.type(text)
        if press_enter:
            self._page.keyboard.press("Enter")
        return self._state()

    def type_text_at(
        self, x: int, y: int, text: str,
        press_enter: bool = False, clear_before_typing: bool = True
    ) -> _EnvState:
        """Click at (x, y), optionally select all, then type *text*."""
        self._page.mouse.click(x, y)
        if clear_before_typing:
            self._page.keyboard.press("Control+a")
        self._page.keyboard.type(text)
        if press_enter:
            self._page.keyboard.press("Enter")
        return self._state()

    def key_combination(self, keys: list[str] | str) -> _EnvState:
        """Press a key combination such as ['Control', 'c'] or 'Control+c'."""
        if isinstance(keys, list):
            combo = "+".join(keys)
        else:
            combo = keys.replace(" ", "+")
        self._page.keyboard.press(combo)
        return self._state()

    def press_key(self, key: str) -> _EnvState:
        """Tap a single key by name (e.g. 'Enter', 'Tab', 'Escape')."""
        self._page.keyboard.press(key)
        return self._state()

    def key_down(self, key: str) -> _EnvState:
        """Hold *key* down without releasing it."""
        self._page.keyboard.down(key)
        return self._state()

    def key_up(self, key: str) -> _EnvState:
        """Release a previously held-down *key*."""
        self._page.keyboard.up(key)
        return self._state()

    # --- Scroll ---

    def scroll_document(self, direction: str) -> _EnvState:
        """Scroll the whole document up or down by 400 px."""
        delta = -400 if direction == "up" else 400
        self._page.evaluate(f"window.scrollBy(0, {delta})")
        return self._state()

    def scroll_at(self, x: int, y: int, direction: str, magnitude: int = 400) -> _EnvState:
        """Move to (x, y) and scroll in *direction* by *magnitude* pixels."""
        dx = dy = 0
        if direction == "up":
            dy = -magnitude
        elif direction == "down":
            dy = magnitude
        elif direction == "left":
            dx = -magnitude
        elif direction == "right":
            dx = magnitude
        self._page.mouse.move(x, y)
        self._page.evaluate(f"window.scrollBy({dx}, {dy})")
        return self._state()

    # --- Misc ---

    def take_screenshot(self) -> _EnvState:
        """Capture and return the current page state."""
        return self._state()

    def wait(self, seconds: int = 1) -> _EnvState:
        """Pause execution for *seconds* (capped at 30) then return state."""
        time.sleep(max(0, min(seconds, 30)))
        return self._state()

    def wait_5_seconds(self) -> _EnvState:
        """Pause for 5 seconds (convenience wrapper around wait)."""
        return self.wait(5)


class _DesktopComputer:
    """Full-desktop computer controlled via pyautogui + mss."""

    def __init__(self):
        """Initialise pyautogui and verify it is installed."""
        try:
            import pyautogui  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "pyautogui no está instalado.\n"
                "Instala con: pip install pyautogui pillow mss\n"
                f"Error: {exc}"
            ) from exc
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    def screen_size(self) -> tuple[int, int]:
        """Return the full-desktop screen dimensions as (width, height)."""
        import pyautogui
        return pyautogui.size()

    def _screenshot_png(self) -> bytes:
        """Grab the full desktop and return it as PNG bytes."""
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                img = sct.grab(monitor)
                return mss.tools.to_png(img.rgb, img.size)
        except ImportError:
            import pyautogui
            buf = io.BytesIO()
            pyautogui.screenshot().save(buf, format="PNG")
            return buf.getvalue()

    def _state(self) -> _EnvState:
        """Capture a desktop screenshot and return it as an EnvState."""
        return _EnvState(screenshot=self._screenshot_png(), url="")

    # --- Navigation ---

    def navigate(self, url: str) -> _EnvState:
        """Open *url* in the default web browser."""
        import webbrowser
        webbrowser.open(url)
        time.sleep(1.5)
        return self._state()

    def go_back(self) -> _EnvState:
        """No-op on desktop; returns the current state."""
        return self._state()

    def go_forward(self) -> _EnvState:
        """No-op on desktop; returns the current state."""
        return self._state()

    def open_web_browser(self) -> _EnvState:
        """Open Google in the default web browser."""
        import webbrowser
        webbrowser.open("https://www.google.com")
        time.sleep(1.5)
        return self._state()

    def search(self) -> _EnvState:
        """No-op on desktop; returns the current state."""
        return self._state()

    # --- Mouse ---

    def click_at(self, x: int, y: int) -> _EnvState:
        """Left-click at screen coordinates (x, y)."""
        import pyautogui
        pyautogui.click(x, y)
        return self._state()

    def double_click_at(self, x: int, y: int) -> _EnvState:
        """Double-click at screen coordinates (x, y)."""
        import pyautogui
        pyautogui.doubleClick(x, y)
        return self._state()

    def triple_click_at(self, x: int, y: int) -> _EnvState:
        """Triple-click at screen coordinates (x, y)."""
        import pyautogui
        pyautogui.tripleClick(x, y)
        return self._state()

    def middle_click_at(self, x: int, y: int) -> _EnvState:
        """Middle-click at screen coordinates (x, y)."""
        import pyautogui
        pyautogui.click(x, y, button="middle")
        return self._state()

    def right_click_at(self, x: int, y: int) -> _EnvState:
        """Right-click at screen coordinates (x, y)."""
        import pyautogui
        pyautogui.rightClick(x, y)
        return self._state()

    def hover_at(self, x: int, y: int) -> _EnvState:
        """Move the mouse pointer to (x, y)."""
        import pyautogui
        pyautogui.moveTo(x, y)
        return self._state()

    def mouse_down(self, x: int, y: int) -> _EnvState:
        """Move to (x, y) and press the left mouse button."""
        import pyautogui
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown()
        return self._state()

    def mouse_up(self, x: int, y: int) -> _EnvState:
        """Move to (x, y) and release the left mouse button."""
        import pyautogui
        pyautogui.moveTo(x, y)
        pyautogui.mouseUp()
        return self._state()

    def drag_and_drop(self, x: int, y: int, destination_x: int, destination_y: int) -> _EnvState:
        """Drag from (x, y) to (destination_x, destination_y)."""
        import pyautogui
        pyautogui.moveTo(x, y)
        pyautogui.dragTo(destination_x, destination_y, button="left", duration=0.5)
        return self._state()

    # --- Keyboard ---

    def type_text(self, text: str, press_enter: bool = False) -> _EnvState:
        """Type *text* into the currently focused element."""
        import pyautogui
        pyautogui.typewrite(text, interval=0.02)
        if press_enter:
            pyautogui.press("enter")
        return self._state()

    def type_text_at(
        self, x: int, y: int, text: str,
        press_enter: bool = False, clear_before_typing: bool = True
    ) -> _EnvState:
        """Click at (x, y), optionally select all, then type *text*."""
        import pyautogui
        pyautogui.click(x, y)
        if clear_before_typing:
            pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(text, interval=0.02)
        if press_enter:
            pyautogui.press("enter")
        return self._state()

    def key_combination(self, keys: list[str] | str) -> _EnvState:
        """Press a key combination via pyautogui.hotkey."""
        import pyautogui
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.replace("+", " ").split()]
        pyautogui.hotkey(*keys)
        return self._state()

    def press_key(self, key: str) -> _EnvState:
        """Tap a single key by name."""
        import pyautogui
        pyautogui.press(key)
        return self._state()

    def key_down(self, key: str) -> _EnvState:
        """Hold *key* down without releasing it."""
        import pyautogui
        pyautogui.keyDown(key)
        return self._state()

    def key_up(self, key: str) -> _EnvState:
        """Release a previously held *key*."""
        import pyautogui
        pyautogui.keyUp(key)
        return self._state()

    # --- Scroll ---

    def scroll_document(self, direction: str) -> _EnvState:
        """Scroll the page up or down by 5 pyautogui scroll clicks."""
        import pyautogui
        clicks = 5 if direction == "down" else -5
        pyautogui.scroll(clicks)
        return self._state()

    def scroll_at(self, x: int, y: int, direction: str, magnitude: int = 400) -> _EnvState:
        """Move to (x, y) and scroll in *direction* by *magnitude* pixels."""
        import pyautogui
        pyautogui.moveTo(x, y)
        clicks = -(magnitude // 80) if direction == "down" else (magnitude // 80)
        if direction in ("left", "right"):
            pyautogui.hscroll(clicks if direction == "right" else -clicks)
        else:
            pyautogui.scroll(clicks)
        return self._state()

    # --- Misc ---

    def take_screenshot(self) -> _EnvState:
        """Capture and return the current desktop state."""
        return self._state()

    def wait(self, seconds: int = 1) -> _EnvState:
        """Pause for *seconds* (capped at 30) then return state."""
        time.sleep(max(0, min(seconds, 30)))
        return self._state()

    def wait_5_seconds(self) -> _EnvState:
        """Pause for 5 seconds (convenience wrapper)."""
        return self.wait(5)


# ---------------------------------------------------------------------------
# Palmiche Computer Use Agent
# ---------------------------------------------------------------------------

_LEGACY_MODELS = [
    "gemini-2.5-computer-use-preview-10-2025",
]

_PREDEFINED_FUNCTIONS = [
    "click", "double_click", "triple_click", "middle_click", "right_click",
    "mouse_down", "mouse_up", "move", "type", "drag_and_drop", "wait",
    "press_key", "key_down", "key_up", "hotkey", "take_screenshot",
    "scroll", "go_back", "navigate", "go_forward",
]

_LEGACY_PREDEFINED_FUNCTIONS = [
    "open_web_browser", "click_at", "hover_at", "type_text_at",
    "scroll_document", "scroll_at", "wait_5_seconds", "go_back",
    "go_forward", "search", "navigate", "key_combination", "drag_and_drop",
]

_MAX_SCREENSHOTS_IN_CONTEXT = 3


class _PalmicheComputerAgent:
    """Agentic loop that uses Gemini computer use to drive a Computer backend."""

    def __init__(self, computer: _PlaywrightComputer | _DesktopComputer, task: str, model: str):
        """Initialise the Gemini client, build config, and take the first screenshot."""
        try:
            from google import genai
            from google.genai import types as gtypes
        except ImportError as exc:
            raise ImportError(
                "google-genai no está instalado.\n"
                "Instala con: pip install google-genai\n"
                f"Error: {exc}"
            ) from exc

        self._computer = computer
        self._task = task
        self._model = model
        self._is_legacy = model in _LEGACY_MODELS

        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY o GEMINI_API_KEY no está configurada.\n"
                "Agrégala a jarvis/.env para usar computer use."
            )

        self._client = genai.Client(api_key=api_key)

        from google.genai import types as gtypes

        env = (
            gtypes.Environment.ENVIRONMENT_BROWSER
            if isinstance(computer, _PlaywrightComputer)
            else gtypes.Environment.ENVIRONMENT_DESKTOP
        )

        self._config = gtypes.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=8192,
            tools=[
                gtypes.Tool(
                    computer_use=gtypes.ComputerUse(environment=env),
                ),
            ],
        )

        initial_state = computer.take_screenshot()
        screenshot_b64 = base64.b64encode(initial_state.screenshot).decode()

        from google.genai.types import Content, Part
        self._contents: list[Content] = [
            Content(
                role="user",
                parts=[
                    Part(text=task),
                    Part(
                        inline_data=gtypes.Blob(
                            mime_type="image/png",
                            data=initial_state.screenshot,
                        )
                    ),
                ],
            )
        ]
        self.final_result: str = ""

    def _handle_action(self, action: Any) -> _EnvState | dict:
        """Dispatch a Gemini function call to the computer backend."""
        name = action.name
        args = action.args or {}

        def dx(v):
            return int(v / 1000 * self._computer.screen_size()[0])

        def dy(v):
            return int(v / 1000 * self._computer.screen_size()[1])

        if name in ("open_web_browser",):
            return self._computer.open_web_browser()
        elif name in ("click", "click_at"):
            return self._computer.click_at(dx(args["x"]), dy(args["y"]))
        elif name == "double_click":
            return self._computer.double_click_at(dx(args["x"]), dy(args["y"]))
        elif name == "triple_click":
            return self._computer.triple_click_at(dx(args["x"]), dy(args["y"]))
        elif name == "middle_click":
            return self._computer.middle_click_at(dx(args["x"]), dy(args["y"]))
        elif name == "right_click":
            return self._computer.right_click_at(dx(args["x"]), dy(args["y"]))
        elif name == "mouse_down":
            return self._computer.mouse_down(dx(args["x"]), dy(args["y"]))
        elif name == "mouse_up":
            return self._computer.mouse_up(dx(args["x"]), dy(args["y"]))
        elif name in ("move", "hover_at"):
            return self._computer.hover_at(dx(args["x"]), dy(args["y"]))
        elif name in ("type",):
            return self._computer.type_text(
                args.get("text", ""), press_enter=args.get("press_enter", False)
            )
        elif name == "type_text_at":
            return self._computer.type_text_at(
                dx(args["x"]), dy(args["y"]), args.get("text", ""),
                press_enter=args.get("press_enter", False),
                clear_before_typing=args.get("clear_before_typing", True),
            )
        elif name == "scroll":
            direction = args["direction"]
            magnitude = args.get("magnitude", 800)
            if direction in ("up", "down"):
                magnitude = dy(magnitude)
            else:
                magnitude = dx(magnitude)
            return self._computer.scroll_at(dx(args["x"]), dy(args["y"]), direction, magnitude)
        elif name == "scroll_document":
            return self._computer.scroll_document(args["direction"])
        elif name == "scroll_at":
            direction = args["direction"]
            magnitude = args.get("magnitude", 800)
            if direction in ("up", "down"):
                magnitude = dy(magnitude)
            else:
                magnitude = dx(magnitude)
            return self._computer.scroll_at(dx(args["x"]), dy(args["y"]), direction, magnitude)
        elif name == "drag_and_drop":
            return self._computer.drag_and_drop(
                dx(args["x"]), dy(args["y"]),
                dx(args["destination_x"]), dy(args["destination_y"]),
            )
        elif name in ("wait",):
            return self._computer.wait(int(args.get("seconds", 1)))
        elif name == "wait_5_seconds":
            return self._computer.wait_5_seconds()
        elif name == "go_back":
            return self._computer.go_back()
        elif name == "go_forward":
            return self._computer.go_forward()
        elif name == "search":
            return self._computer.search()
        elif name == "navigate":
            return self._computer.navigate(args["url"])
        elif name in ("hotkey", "key_combination"):
            keys = args.get("keys", "")
            return self._computer.key_combination(keys)
        elif name == "press_key":
            return self._computer.press_key(args["key"])
        elif name == "key_down":
            return self._computer.key_down(args["key"])
        elif name == "key_up":
            return self._computer.key_up(args["key"])
        elif name == "take_screenshot":
            return self._computer.take_screenshot()
        else:
            return {"error": f"Acción no soportada: {name}"}

    def _run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE"]:
        """Call Gemini once, dispatch all returned function calls, and return status."""
        from google.genai.types import Content, Part, FunctionResponse, FinishReason

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=self._contents,
                config=self._config,
            )
        except Exception as exc:
            self.final_result = f"Error al llamar a Gemini: {exc}"
            return "COMPLETE"

        if not response.candidates:
            return "COMPLETE"

        candidate = response.candidates[0]
        if candidate.content:
            self._contents.append(candidate.content)

        # Collect text parts for final result
        text_parts = []
        function_calls = []
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)
                if hasattr(part, "function_call") and part.function_call:
                    function_calls.append(part.function_call)

        if not function_calls:
            self.final_result = " ".join(text_parts) or "Tarea completada."
            return "COMPLETE"

        # Check for malformed function call with no text
        finish_reason = getattr(candidate, "finish_reason", None)
        if not function_calls and not text_parts and str(finish_reason) == "MALFORMED_FUNCTION_CALL":
            return "CONTINUE"

        # Execute each function call
        function_responses = []
        all_functions = _PREDEFINED_FUNCTIONS + _LEGACY_PREDEFINED_FUNCTIONS
        for fc in function_calls:
            # Safety confirmation check
            if fc.args and (safety := fc.args.get("safety_decision")):
                if isinstance(safety, dict) and safety.get("decision") == "require_confirmation":
                    print(f"\n⚠️  Gemini solicita confirmación: {safety.get('explanation', '')}")
                    answer = input("¿Continuar? [s/N]: ").strip().lower()
                    if answer not in ("s", "si", "sí", "y", "yes"):
                        self.final_result = "Tarea cancelada por el usuario."
                        return "COMPLETE"

            fc_result = self._handle_action(fc)

            if isinstance(fc_result, _EnvState):
                function_responses.append(
                    FunctionResponse(
                        name=fc.name,
                        response={"url": fc_result.url},
                        parts=[
                            Part(
                                inline_data=_blob_from_bytes(fc_result.screenshot)
                            )
                        ],
                    )
                )
            else:
                function_responses.append(
                    FunctionResponse(name=fc.name, response=fc_result or {})
                )

        self._contents.append(
            Content(
                role="user",
                parts=[Part(function_response=fr) for fr in function_responses],
            )
        )

        # Prune old screenshots to keep context window manageable
        self._prune_old_screenshots(all_functions)
        return "CONTINUE"

    def _prune_old_screenshots(self, predefined_fns: list[str]) -> None:
        """Remove screenshots from older turns, keeping only the most recent ones."""
        from google.genai.types import Part

        turns_with_screenshots = 0
        for content in reversed(self._contents):
            if content.role != "user" or not content.parts:
                continue
            has_screenshot = any(
                getattr(p, "function_response", None)
                and getattr(p.function_response, "parts", None)
                and p.function_response.name in predefined_fns
                for p in content.parts
            )
            if not has_screenshot:
                continue
            turns_with_screenshots += 1
            if turns_with_screenshots > _MAX_SCREENSHOTS_IN_CONTEXT:
                for p in content.parts:
                    fr = getattr(p, "function_response", None)
                    if fr and getattr(fr, "parts", None) and fr.name in predefined_fns:
                        fr.parts = None

    def run(self, max_iterations: int = 30) -> str:
        """Execute the agent loop and return the final textual result."""
        for _ in range(max_iterations):
            status = self._run_one_iteration()
            if status == "COMPLETE":
                break
        return self.final_result or "Tarea finalizada (límite de iteraciones alcanzado)."


def _blob_from_bytes(data: bytes):
    """Create a google.genai Blob part from PNG bytes."""
    from google.genai import types as gtypes
    return gtypes.Blob(mime_type="image/png", data=data)


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------


def computer_use_task(
    task: str,
    backend: str = "",
    initial_url: str = "https://www.google.com",
    max_iterations: int = 0,
    model: str = "",
    headless: bool = True,
) -> str:
    """Execute a computer use task using Gemini visual intelligence.

    Palmiche-AI will take control of a browser (or the full desktop) and
    complete the task step-by-step using Gemini's computer use capability.

    Args:
        task: Natural language description of what to do (e.g. "Search for
              the weather in Havana and tell me the temperature").
        backend: "playwright" for browser control or "desktop" for full
                 desktop control. Defaults to COMPUTER_USE_BACKEND env var.
        initial_url: Starting URL when using the playwright backend.
        max_iterations: Safety cap on agent loop iterations. Defaults to
                        COMPUTER_USE_MAX_ITERATIONS env var.
        model: Gemini model to use. Defaults to COMPUTER_USE_MODEL env var
               or "gemini-2.5-flash".
        headless: Run browser in headless mode (no visible window). Default
                  True; set False for debugging.

    Returns:
        A text summary of what was accomplished.
    """
    from ..config import COMPUTER_USE_BACKEND, COMPUTER_USE_MAX_ITERATIONS, COMPUTER_USE_MODEL, GOOGLE_API_KEY

    resolved_model = model or COMPUTER_USE_MODEL or "gemini-2.5-flash"
    resolved_backend = backend or COMPUTER_USE_BACKEND or "playwright"
    resolved_max_iterations = max_iterations or COMPUTER_USE_MAX_ITERATIONS or 30

    if not GOOGLE_API_KEY:
        return (
            "Error: GOOGLE_API_KEY no está configurada. "
            "Agrégala a jarvis/.env para usar computer use."
        )

    resolved_backend = resolved_backend.strip().lower()

    if resolved_backend == "desktop":
        computer: _DesktopComputer | _PlaywrightComputer = _DesktopComputer()
        agent = _PalmicheComputerAgent(computer, task, resolved_model)
        try:
            return agent.run(resolved_max_iterations)
        finally:
            pass
    else:
        # Playwright's sync API raises an error when called inside an already-running
        # asyncio event loop (tray mode / ADK backend / any async context).
        # Running in a dedicated thread gives a clean environment with no event loop,
        # so playwright can create its own without conflict.
        import concurrent.futures

        def _run_playwright() -> str:
            computer = _PlaywrightComputer(initial_url=initial_url, headless=headless)
            try:
                return _PalmicheComputerAgent(computer, task, resolved_model).run(resolved_max_iterations)
            finally:
                computer.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(_run_playwright).result()
