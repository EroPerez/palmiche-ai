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

# El usuario real: quien ejecutó sudo (no root). Permite sobreescribir con
# JARVIS_USER=otro sudo ./install-power-rules.sh
TARGET_USER="${JARVIS_USER:-${SUDO_USER:-$(logname 2>/dev/null || true)}}"
if [ -z "$TARGET_USER" ] || [ "$TARGET_USER" = "root" ]; then
    echo "Error: no se pudo determinar tu usuario. Ejecuta con sudo desde tu"
    echo "sesión, o indícalo: JARVIS_USER=tu_usuario sudo $0"
    exit 1
fi

echo "→ Instalando $RULE_DST (usuario: $TARGET_USER)"
sed "s/__JARVIS_USER__/$TARGET_USER/g" "$RULE_SRC" > "$RULE_DST"
chmod 0644 "$RULE_DST"

echo "→ Reiniciando polkit"
if command -v systemctl >/dev/null 2>&1; then
    systemctl restart polkit 2>/dev/null || systemctl restart polkitd 2>/dev/null || true
fi

echo ""
echo "  ✓ Regla instalada. Apagar/reiniciar/suspender ya no pedirán contraseña"
echo "    para el usuario: $TARGET_USER"
