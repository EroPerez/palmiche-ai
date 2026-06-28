#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/jarvis/.venv/bin/activate"
# Force offscreen Qt backend so cv2 (opencv-python) never tries to load
# dxcb/xcb plugins, which it doesn't ship and which cause a hard SIGABRT.
export QT_QPA_PLATFORM=offscreen
python3 -m jarvis "$@"
