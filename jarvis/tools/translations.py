"""English overlay for the Spanish tool/skill catalog.

The canonical tool definitions in ``registry.py`` are written in Spanish. Many
LLMs invoke tools more reliably when the tool *schemas* (names, descriptions,
parameter docs) are in English, even while still replying to the user in their
own language. This module provides an English text overlay so each brain can
present its skills in either language without duplicating the schema structure
(types, enums, ``required`` lists stay in a single source of truth).

Usage::

    from .registry import TOOL_DEFINITIONS
    from .translations import localize_definitions
    english_defs = localize_definitions(TOOL_DEFINITIONS, "en")

The overlay is keyed by tool name. The special key ``"_"`` holds the tool-level
description; every other key maps a parameter name to its English description.
Anything missing from the overlay falls back to the original Spanish text, so a
newly added tool keeps working even before it is translated.
"""
from __future__ import annotations

import copy

# Languages this module knows how to produce. Anything else is treated as the
# canonical Spanish (no overlay applied).
SUPPORTED_LANGS = ("es", "en")

# ---------------------------------------------------------------------------
# English text catalog — keyed by tool name.
#   "_"        → tool-level description
#   <param>    → that parameter's description
# ---------------------------------------------------------------------------
TOOL_TEXT_EN: dict[str, dict[str, str]] = {
    "get_system_info": {
        "_": "Get system information: CPU, RAM, disk, uptime",
    },
    "get_battery_info": {
        "_": "Get battery status: percentage, charging state, time remaining",
    },
    "control_volume": {
        "_": "Control system volume (get/set/up/down/mute/unmute)",
        "action": "Volume action",
        "value": "Value 0-100 for 'set', or step for 'up'/'down'",
    },
    "control_brightness": {
        "_": "Control screen brightness (get/set/up/down). Linux: requires brightnessctl.",
        "action": "Brightness action",
        "value": "Value 0-100 for 'set', or step for 'up'/'down'",
    },
    "power_action": {
        "_": (
            "Control the power state: shut down, restart, sleep or lock the screen. "
            "For shutdown/restart/sleep, ask the user for explicit confirmation before "
            "calling this tool with confirmed=true."
        ),
        "action": "Power action",
        "confirmed": "The user explicitly confirmed this destructive action",
    },
    "open_application": {
        "_": "Open an application or program",
        "name": "Application name or command (e.g. firefox, code, spotify, nautilus)",
    },
    "close_application": {
        "_": "Close an application by process name",
        "name": "Name of the process to close",
        "force": "Force immediate close (SIGKILL). Default: false (SIGTERM)",
        "confirmed": "The user explicitly confirmed closing this application. Pass true after getting confirmation.",
    },
    "list_running_apps": {
        "_": "List running processes/applications with memory usage",
        "filter": "Optional filter by process name",
    },
    "search_files": {
        "_": "Search for files or directories in the filesystem",
        "pattern": "Name or pattern to search for (e.g. '*.pdf', 'project')",
        "directory": "Directory to search in. Default: ~ (home)",
        "file_type": "Item type. Default: any",
    },
    "open_file": {
        "_": "Open a file with the system's default application",
        "path": "Path to the file",
    },
    "list_directory": {
        "_": "List the contents of a directory",
        "path": "Directory path. Default: ~ (home)",
        "show_hidden": "Show hidden files (those starting with a dot)",
    },
    "read_file": {
        "_": "Read the contents of a text file",
        "path": "Path to the file",
        "max_lines": "Maximum number of lines to read. Default: 100",
    },
    "create_directory": {
        "_": "Create a directory (including parent directories if missing)",
        "path": "Path of the directory to create",
    },
    "open_url": {
        "_": "Open a URL in the default browser",
        "url": "URL to open",
    },
    "web_search": {
        "_": "Open a web search in the browser in incognito/private mode to leave no history. Default: Google.",
        "query": "Search term",
        "engine": "Search engine. Default: google",
    },
    "get_clipboard": {
        "_": "Get the current clipboard contents",
    },
    "set_clipboard": {
        "_": "Write text to the clipboard",
        "text": "Text to copy",
    },
    "send_notification": {
        "_": "Send a desktop notification",
        "title": "Title",
        "message": "Message body",
        "urgency": "Urgency level. Default: normal",
    },
    "run_shell_command": {
        "_": (
            "Run an arbitrary shell command. "
            "Use only when there is no dedicated tool. Timeout: 30 seconds. "
            "Explain to the user what the command will do and confirm before calling with confirmed=true. "
            "If the command uses sudo and JARVIS_SUDO_PASSWORD is set, the password is passed automatically. "
            "If the command fails due to insufficient permissions, the result will say so and you may retry with use_sudo=true "
            "after informing the user and getting their confirmation."
        ),
        "command": "Command to run",
        "working_dir": "Working directory. Default: ~",
        "confirmed": "The user confirmed that this command may run",
        "use_sudo": (
            "Retry the command with sudo. Use when a previous command failed due to permissions. "
            "Requires user confirmation and JARVIS_SUDO_PASSWORD to be set."
        ),
    },
    "write_file": {
        "_": "Write or append content to a text file",
        "path": "Target file path",
        "content": "Content to write",
        "mode": "'write' to overwrite (default) or 'append' to add to the end",
        "confirmed": "The user explicitly confirmed the write/overwrite. Pass true after getting confirmation.",
    },
    "delete_file": {
        "_": "Delete a file or empty directory",
        "path": "Path of the file or directory to delete",
        "confirmed": "The user explicitly confirmed the deletion. Pass true after getting confirmation.",
    },
    "move_file": {
        "_": "Move or rename a file or directory",
        "source": "Source path",
        "destination": "Destination path",
        "confirmed": "The user explicitly confirmed the operation. Pass true after getting confirmation.",
    },
    "copy_file": {
        "_": "Copy a file or directory to another location",
        "source": "Source path",
        "destination": "Destination path",
    },
    "get_network_info": {
        "_": "Get local IP, public IP, WiFi SSID and network status",
    },
    "ping_host": {
        "_": "Ping a host and return latency and packet loss",
        "host": "Hostname or IP to ping",
        "count": "Number of packets to send (1-10). Default: 4",
    },
    "media_control": {
        "_": "Control media playback: music, video (play/pause/next/previous/stop/status)",
        "action": "Playback action",
    },
    "get_media_status": {
        "_": "Get the title, artist and current state of the active media player",
    },
    "take_screenshot": {
        "_": "Take a screenshot and save it to a file",
        "path": "Target file path. If omitted, saved to ~/Capturas/ with a timestamp",
        "selection": "If true, lets you select a screen area",
    },
    "setup_autostart": {
        "_": "Enable or disable Jarvis autostart with the system",
        "enable": "True to enable autostart, False to disable it",
        "tray": "If True, start in system tray mode (default: True)",
        "backend": "Backend to use on startup. Default: anthropic",
        "confirmed": "The user explicitly confirmed the autostart configuration change. Pass true after getting confirmation.",
    },
    "add_event": {
        "_": "Create an event in the local calendar. Date in YYYY-MM-DD (or 'hoy'/'mañana'), optional time HH:MM.",
        "title": "Event title",
        "date": "Date YYYY-MM-DD or 'hoy'/'mañana'",
        "time": "Time HH:MM (24h), optional",
        "description": "Optional description",
        "location": "Optional location",
    },
    "list_events": {
        "_": "List calendar events sorted by date. Accepts an optional start/end range (YYYY-MM-DD).",
        "start": "Range start date (YYYY-MM-DD), optional",
        "end": "Range end date (YYYY-MM-DD), optional",
    },
    "upcoming_events": {
        "_": "List upcoming events from today for N days (default 7).",
        "days": "Number of days ahead (default 7)",
    },
    "delete_event": {
        "_": "Delete a calendar event by its id (the one shown in brackets when listing).",
        "event_id": "Id of the event to delete",
    },
    "format_json": {
        "_": "Validate and pretty-print a JSON string.",
        "text": "JSON string to format",
        "indent": "Indentation spaces (default 2)",
    },
    "hash_text": {
        "_": "Compute the hash of a text (md5, sha1, sha256 or sha512).",
        "text": "Text to hash",
        "algorithm": "Algorithm (default sha256)",
    },
    "encode_decode": {
        "_": "Encode or decode text with base64, url or hex.",
        "text": "Input text",
        "scheme": "Scheme (default base64)",
        "operation": "Operation (default encode)",
    },
    "generate_uuid": {
        "_": "Generate one or more random UUID4 values.",
        "count": "Number of UUIDs (default 1, max 50)",
    },
    "convert_timestamp": {
        "_": "Convert between Unix epoch and ISO-8601. Use 'now' for the current time.",
        "value": "Epoch (number), ISO-8601 date, or 'now'",
    },
    "http_request": {
        "_": (
            "Make an HTTP request and return status, key headers and a body preview. Useful for testing APIs. "
            "GET/HEAD need no confirmation. POST/PUT/PATCH/DELETE mutate external state: inform the user and call with confirmed=true."
        ),
        "url": "URL to request",
        "method": "HTTP method (default GET)",
        "body": "Request body (for POST/PUT/PATCH)",
        "confirmed": "The user confirmed the mutating request (POST/PUT/PATCH/DELETE). Not required for GET/HEAD.",
    },
    "git_status": {
        "_": "Show branch, working-tree status and latest commits of a git repository.",
        "path": "Repository path (default: current directory)",
    },
    "find_process_on_port": {
        "_": "Show which process is listening on a TCP port.",
        "port": "Port number",
    },
    "get_weather": {
        "_": (
            "Get current weather for a city (temperature, humidity, wind, visibility). "
            "If no city is given, uses IP-based location. No API key required."
        ),
        "city": "City or place (e.g. 'Madrid', 'New York'). Empty = detect by IP.",
        "units": "Unit system: metric (°C, km/h) or imperial (°F, mph). Default: metric.",
    },
    "get_forecast": {
        "_": "Get the weather forecast for the next 1-3 days.",
        "city": "City or place. Empty = detect by IP.",
        "days": "Number of forecast days (1-3). Default: 3.",
        "units": "Unit system. Default: metric.",
    },
    "create_note": {
        "_": "Create or update a personal note with title, content and optional tags.",
        "title": "Note title",
        "content": "Note content",
        "tags": "Comma-separated tags (e.g. 'work, ideas')",
    },
    "list_notes": {
        "_": "List all saved notes, optionally filtered by tag.",
        "tag": "Filter by tag (optional)",
    },
    "read_note": {
        "_": "Read the full content of a note by title or id.",
        "title": "Note title or id",
    },
    "search_notes": {
        "_": "Search notes by title or content.",
        "query": "Search term",
    },
    "delete_note": {
        "_": "Delete a note by title or id.",
        "title": "Title or id of the note to delete",
    },
    "set_timer": {
        "_": (
            "Start a timer that sends a desktop notification when it finishes. "
            "Runs in the background; the process must stay alive."
        ),
        "seconds": "Duration in seconds (max 86400 = 24h)",
        "label": "Timer description (optional)",
    },
    "set_alarm": {
        "_": "Set an alarm for a specific time of day (HH:MM, 24h). If it already passed, it is scheduled for tomorrow.",
        "alarm_time": "Alarm time in HH:MM format (e.g. '08:30', '14:00')",
        "label": "Alarm description (optional)",
    },
    "list_timers": {
        "_": "Show all active timers with time remaining.",
    },
    "cancel_timer": {
        "_": "Cancel an active timer by its id.",
        "timer_id": "Timer id (6 characters)",
    },
    "calculate": {
        "_": (
            "Safely evaluate math expressions. Supports +−×÷^, sqrt, sin/cos/tan, "
            "log, abs, round, factorial, and constants pi/e. E.g. 'sqrt(144)', '2^10', 'sin(pi/2)'."
        ),
        "expression": "Math expression to evaluate",
    },
    "convert_units": {
        "_": (
            "Convert between units of measure. Categories: length (m, km, mi, ft, in…), "
            "mass (kg, g, lb, oz…), temperature (°C, °F, K), speed (km/h, mph, m/s, kt), "
            "area, volume, digital storage (GB, MB…)."
        ),
        "value": "Numeric value to convert",
        "from_unit": "Source unit (e.g. 'km', 'lb', '°C', 'GB')",
        "to_unit": "Target unit (e.g. 'mi', 'kg', '°F', 'MB')",
    },
    "text_stats": {
        "_": "Analyze a text and return statistics: words, characters, lines, sentences and estimated reading time.",
        "text": "Text to analyze",
    },
    "text_transform": {
        "_": (
            "Transform a text by applying an operation. Available operations: "
            "upper, lower, title, capitalize, reverse, trim, slug, snake, camel, pascal, "
            "strip_accents, count_vowels, palindrome."
        ),
        "text": "Text to transform",
        "operation": "Transformation to apply",
    },
    "fetch_webpage": {
        "_": (
            "Download and extract the readable text of a web page (strips HTML, scripts and styles). "
            "Useful for reading articles, documentation or any web content."
        ),
        "url": "URL of the page to read",
        "max_chars": "Maximum characters to return (500-10000, default 3000)",
    },
    "get_rss_feed": {
        "_": "Get the latest entries of an RSS or Atom feed: title, link and publication date.",
        "url": "URL of the RSS/Atom feed",
        "max_items": "Maximum number of entries to show (default 10)",
    },
    "camera_capture": {
        "_": "Capture a photo from the system camera and save it to a file.",
        "save_path": "Path to save the image. Default: ~/Capturas/camera_TIMESTAMP.jpg",
        "camera_index": "Camera device index (0=default). -1 uses the configured default.",
        "show_preview": "Show the captured frame in a preview window. Default: false.",
    },
    "camera_describe": {
        "_": (
            "Capture a photo from the camera and describe the scene using the configured multimodal AI model. Identifies people, objects, colors, environment and details."
        ),
        "prompt": "Custom prompt for the AI. Default: general scene description.",
        "camera_index": "Camera device index. -1 uses the configured default.",
        "save_path": "Optional path to save the captured image.",
        "show_preview": "Show the captured frame in a preview window while analyzing. Default: false.",
    },
    "camera_recognize_objects": {
        "_": (
            "Capture a photo from the camera and identify all visible objects "
            "with position, relative size and confidence level. Uses the configured multimodal AI model."
        ),
        "camera_index": "Camera device index. -1 uses the configured default.",
        "save_path": "Optional path to save the captured image.",
        "show_preview": "Show the captured frame in a preview window while analyzing. Default: false.",
    },
    "camera_recognize_gestures": {
        "_": (
            "Capture a photo from the camera and recognize hand gestures and body language. "
            "Detects: thumbs up, peace sign, fist, open palm, pointing, pinch, OK, etc. "
            "Uses the configured multimodal AI model."
        ),
        "camera_index": "Camera device index. -1 uses the configured default.",
        "save_path": "Optional path to save the captured image.",
        "show_preview": "Show the captured frame in a preview window while analyzing. Default: false.",
    },
    "camera_analyze": {
        "_": (
            "Capture a photo and analyze it with a custom prompt. "
            "Flexible: 'how many people?', 'what color is the shirt?', "
            "'is the door open?', 'read the text on the sign', etc."
        ),
        "prompt": "Question or instruction about what the camera sees.",
        "camera_index": "Camera device index. -1 uses the configured default.",
        "save_path": "Optional path to save the captured image.",
        "show_preview": "Show the captured frame in a preview window while analyzing. Default: false.",
    },
    "camera_monitor": {
        "_": (
            "Monitor the camera for a period, analyzing frames at regular intervals. "
            "Useful for detecting changes, counting people, watching activity or waiting for specific events."
        ),
        "task": "What to monitor (e.g. 'count people', 'detect movement'). Default: general changes.",
        "duration": "Monitoring duration in seconds (max 60). Default: 10.",
        "interval": "Seconds between captures (min 2). Default: 3.",
        "camera_index": "Camera device index. -1 uses the configured default.",
        "show_preview": "Show a live preview window while monitoring. Default: false.",
    },
    "camera_preview": {
        "_": (
            "Open a live camera preview window showing what the camera sees in real time. "
            "No AI analysis is performed — purely for viewing the camera feed."
        ),
        "duration": "Preview duration in seconds (max 120). Default: 15.",
        "camera_index": "Camera device index. -1 uses the configured default.",
    },
    "computer_use_task": {
        "_": (
            "Visually control a web browser or the full desktop to complete a task "
            "using Gemini's visual intelligence (computer use). "
            "Use this tool when the user asks to perform complex web actions, "
            "fill forms, navigate pages, take guided screenshots, or "
            "automate any visual task. Requires GOOGLE_API_KEY."
        ),
        "task": "Natural-language description of the task to perform (e.g. 'Look up the weather in Havana and tell me the temperature')",
        "backend": "'playwright' to control a Chromium browser (default), 'desktop' to control the full desktop",
        "initial_url": "Initial URL for the playwright backend (default: https://www.google.com)",
        "max_iterations": "Agent iteration limit (default: 30)",
    },
}


def localize_definitions(definitions: list[dict], lang: str = "en") -> list[dict]:
    """Return a copy of *definitions* with descriptions overlaid in *lang*.

    For ``lang == "en"`` the English overlay is applied on top of the canonical
    Spanish schema. For any other language (including ``"es"``) the definitions
    are returned unchanged. Tools or parameters missing from the overlay keep
    their original text, so the result is always complete.
    """
    if lang != "en":
        return definitions

    out: list[dict] = []
    for d in definitions:
        text = TOOL_TEXT_EN.get(d.get("name", ""))
        if not text:
            out.append(d)
            continue
        nd = copy.deepcopy(d)
        if "_" in text:
            nd["description"] = text["_"]
        props = nd.get("input_schema", {}).get("properties", {})
        for pname, pinfo in props.items():
            if pname in text and isinstance(pinfo, dict):
                pinfo["description"] = text[pname]
        out.append(nd)
    return out
