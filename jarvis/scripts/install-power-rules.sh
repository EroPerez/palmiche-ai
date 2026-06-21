#!/bin/bash
# Install the Jarvis polkit rule so power actions (apagar/reiniciar/suspender)
# run without an interactive password prompt for the active local session.
#
# Usage:
#   sudo ./install-power-rules.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULE_SRC="$SCRIPT_DIR/49-jarvis-power.rules"
RULE_DST="/etc/polkit-1/rules.d/49-jarvis-power.rules"

if [ "$(id -u)" -ne 0 ]; then
    echo "Este script necesita privilegios de root. Ejecuta:"
    echo "  sudo $0"
    exit 1
fi

if [ ! -d /etc/polkit-1/rules.d ]; then
    echo "Error: /etc/polkit-1/rules.d no existe."
    echo "Tu sistema podría usar una versión antigua de polkit (.pkla) o no tener polkit."
    exit 1
fi

echo "→ Instalando $RULE_DST"
install -m 0644 "$RULE_SRC" "$RULE_DST"

echo "→ Reiniciando polkit"
if command -v systemctl >/dev/null 2>&1; then
    systemctl restart polkit 2>/dev/null || systemctl restart polkitd 2>/dev/null || true
fi

echo ""
echo "  ✓ Regla instalada. Apagar/reiniciar/suspender ya no pedirán contraseña"
echo "    para la sesión local activa."
