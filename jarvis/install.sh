#!/usr/bin/env bash
# =============================================================================
#  Palmiche-AI — Instalador interactivo
#  Instala J.A.R.V.I.S y sus módulos opcionales en un entorno virtual Python.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ─── Colores ─────────────────────────────────────────────────────────────────
_G='\033[0;32m'   # verde
_BG='\033[1;32m'  # verde brillante
_DG='\033[2;32m'  # verde tenue
_CY='\033[0;36m'  # cyan
_YL='\033[1;33m'  # amarillo
_RD='\033[0;31m'  # rojo
_WH='\033[1;37m'  # blanco
_DIM='\033[2m'    # dim
_NC='\033[0m'     # reset

# ─── Utilidades ──────────────────────────────────────────────────────────────
_width=70

_print_center() {
    local text="$1" color="${2:-$_NC}"
    local len="${#text}"
    local pad=$(( (_width - len) / 2 ))
    printf "%${pad}s${color}%s${_NC}%${pad}s\n" "" "$text" ""
}

_hr() {
    printf "${_DG}%${_width}s${_NC}\n" | tr ' ' '─'
}

_progress_bar() {
    local label="$1" pct="$2"
    local filled=$(( pct * 40 / 100 ))
    local empty=$(( 40 - filled ))
    printf "  ${_DIM}%-22s${_NC} ${_DG}[${_NC}" "$label"
    printf "${_BG}%${filled}s${_NC}" | tr ' ' '█'
    printf "${_DIM}%${empty}s${_NC}" | tr ' ' '░'
    printf "${_DG}]${_NC} ${_BG}%3d%%${_NC}\n" "$pct"
}

_ok()   { printf "  ${_BG}✓${_NC}  %s\n" "$1"; }
_warn() { printf "  ${_YL}⚠${_NC}  %s\n" "$1"; }
_err()  { printf "  ${_RD}✗${_NC}  %s\n" "$1"; }
_info() { printf "  ${_CY}→${_NC}  %s\n" "$1"; }

# ─── Splash screen ───────────────────────────────────────────────────────────
_splash() {
    clear
    echo ""
    _hr
    echo ""
    _print_center "██████╗  █████╗ ██╗     ███╗   ███╗██╗ ██████╗██╗  ██╗███████╗" "$_BG"
    _print_center "██╔══██╗██╔══██╗██║     ████╗ ████║██║██╔════╝██║  ██║██╔════╝" "$_BG"
    _print_center "██████╔╝███████║██║     ██╔████╔██║██║██║     ███████║█████╗  " "$_BG"
    _print_center "██╔═══╝ ██╔══██║██║     ██║╚██╔╝██║██║██║     ██╔══██║██╔══╝  " "$_BG"
    _print_center "██║     ██║  ██║███████╗██║ ╚═╝ ██║██║╚██████╗██║  ██║███████╗" "$_BG"
    _print_center "╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝" "$_BG"
    echo ""
    _print_center "A  I" "$_DG"
    echo ""
    _hr
    echo ""
    _print_center "J.A.R.V.I.S — Just A Rather Very Intelligent System" "$_CY"
    _print_center "Asistente personal con IA para tu laptop" "$_DIM"
    echo ""
    _hr
    echo ""
}

# ─── Animación de carga ───────────────────────────────────────────────────────
_loading_animation() {
    local label="$1"
    local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local i=0
    while true; do
        printf "\r  ${_BG}${frames[$i]}${_NC}  ${_DIM}%s...${_NC}" "$label"
        i=$(( (i + 1) % ${#frames[@]} ))
        sleep 0.08
    done
}

_run_with_spinner() {
    local label="$1"
    shift
    _loading_animation "$label" &
    local spin_pid=$!
    "$@" >/dev/null 2>&1
    local exit_code=$?
    kill "$spin_pid" 2>/dev/null
    wait "$spin_pid" 2>/dev/null
    printf "\r"
    if [ $exit_code -eq 0 ]; then
        _ok "$label"
    else
        _warn "$label (puede requerir dependencias del sistema)"
    fi
    return $exit_code
}

# ─── Verificaciones de sistema ────────────────────────────────────────────────
_check_system() {
    echo ""
    _info "Verificando requisitos del sistema..."
    echo ""

    # Python 3.10+
    if ! command -v python3 &>/dev/null; then
        _err "Python 3 no encontrado. Instálalo antes de continuar."
        exit 1
    fi

    local py_ver
    py_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local py_major py_minor
    py_major=$(echo "$py_ver" | cut -d. -f1)
    py_minor=$(echo "$py_ver" | cut -d. -f2)

    if [ "$py_major" -lt 3 ] || { [ "$py_major" -eq 3 ] && [ "$py_minor" -lt 10 ]; }; then
        _err "Se requiere Python 3.10+. Versión detectada: $py_ver"
        exit 1
    fi
    _ok "Python $py_ver"

    # pip
    if ! python3 -m pip --version &>/dev/null; then
        _err "pip no encontrado. Instálalo con: sudo apt install python3-pip"
        exit 1
    fi
    _ok "pip disponible"

    echo ""
}

# ─── Entorno virtual ──────────────────────────────────────────────────────────
_setup_venv() {
    if [ ! -d ".venv" ]; then
        _info "Creando entorno virtual Python..."
        python3 -m venv .venv
        _ok "Entorno virtual creado"
    else
        _ok "Entorno virtual existente reutilizado"
    fi
    source .venv/bin/activate
    _run_with_spinner "Actualizando pip" pip install --upgrade pip
}

# ─── Instalación de dependencias ──────────────────────────────────────────────
_pip_install() {
    local label="$1"
    shift
    _run_with_spinner "$label" pip install --quiet "$@"
}

_install_group() {
    local group="$1"
    case "$group" in
        core)
            _pip_install "Núcleo (anthropic, rich, psutil…)" -r requirements.txt
            ;;
        voice)
            _pip_install "Reconocimiento de voz (SpeechRecognition)" SpeechRecognition pyttsx3 gtts
            if ! _pip_install "Audio (pyaudio)" pyaudio 2>/dev/null; then
                _warn "pyaudio falló — instala: sudo apt install portaudio19-dev python3-pyaudio"
            fi
            ;;
        tray)
            _pip_install "GUI / Bandeja (PyQt6)" PyQt6 "PyQt6-Qt6-Multimedia" Pillow
            ;;
        adk)
            _pip_install "Google ADK + LiteLLM" google-adk litellm
            ;;
        gemini)
            _pip_install "Google ADK (nativo Gemini)" google-adk
            ;;
        ollama)
            _info "Ollama usa el servidor local — no requiere paquetes Python extra."
            _info "Instala el servidor desde: https://ollama.ai"
            _info "Luego descarga un modelo: ollama pull llama3.2"
            ;;
        a2a)
            _pip_install "Servidor A2A (FastAPI + uvicorn)" fastapi uvicorn
            ;;
        mcp)
            _pip_install "Soporte MCP (Model Context Protocol)" mcp
            ;;
        computer-use)
            _pip_install "Computer Use (google-genai)" google-genai
            _pip_install "Computer Use (playwright)" playwright
            _pip_install "Computer Use (pyautogui + mss)" pyautogui Pillow mss
            _info "Instalando navegador Chromium para Playwright..."
            if python3 -m playwright install chromium >/dev/null 2>&1; then
                _ok "Chromium instalado"
            else
                _warn "playwright install chromium falló — puede requerir: sudo apt install libnss3 libatk1.0-0"
            fi
            ;;
        assets)
            _pip_install "Extractor de assets (yt-dlp)" yt-dlp
            ;;
    esac
}

# ─── Configuración .env ───────────────────────────────────────────────────────
_setup_env() {
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo ""
        _warn "Se creó jarvis/.env desde .env.example"
        _warn "Edita jarvis/.env y agrega tus API keys:"
        echo ""
        echo "     ${_CY}ANTHROPIC_API_KEY${_NC}  → https://console.anthropic.com/"
        echo "     ${_CY}GOOGLE_API_KEY${_NC}     → https://aistudio.google.com/app/apikey"
        echo ""
    else
        _ok ".env ya existe, no se sobreescribió"
    fi
}

# ─── Script lanzador ──────────────────────────────────────────────────────────
_create_launcher() {
    cat > "$SCRIPT_DIR/../run_jarvis.sh" << 'LAUNCHER'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/jarvis/.venv/bin/activate"
python3 -m jarvis "$@"
LAUNCHER
    chmod +x "$SCRIPT_DIR/../run_jarvis.sh"
    _ok "Lanzador creado: run_jarvis.sh"
}

# ─── Resumen final ────────────────────────────────────────────────────────────
_print_summary() {
    echo ""
    _hr
    echo ""
    _print_center "✓  Palmiche-AI instalado correctamente" "$_BG"
    echo ""
    _hr
    echo ""
    echo "  ${_WH}Uso rápido:${_NC}"
    echo ""
    echo "    ${_BG}./run_jarvis.sh${_NC}                          ${_DIM}# Modo interactivo${_NC}"
    echo "    ${_BG}./run_jarvis.sh -q '¿cuánta RAM tengo?'${_NC}  ${_DIM}# Consulta rápida${_NC}"
    echo "    ${_BG}./run_jarvis.sh --voice${_NC}                  ${_DIM}# Con reconocimiento de voz${_NC}"
    echo "    ${_BG}./run_jarvis.sh --tray${_NC}                   ${_DIM}# Bandeja del sistema (GUI)${_NC}"
    echo "    ${_BG}./run_jarvis.sh --backend gemini${_NC}         ${_DIM}# Usar Gemini como backend${_NC}"
    echo ""
    echo "  ${_WH}Computer Use (navegador visual):${_NC}"
    echo ""
    echo "    ${_CY}\"Busca el clima en La Habana usando el navegador\"${_NC}"
    echo "    ${_CY}\"Abre YouTube y pon música de jazz\"${_NC}"
    echo ""
    echo "  ${_WH}Documentación:${_NC} INSTALL.md · README.md · docs/ARCHITECTURE.md"
    echo ""
    _hr
    echo ""
}

# ─── Menú interactivo ─────────────────────────────────────────────────────────
_print_menu() {
    echo ""
    _print_center "¿Qué deseas instalar?" "$_WH"
    echo ""
    echo "  ${_BG}[1]${_NC}  ${_WH}Todo${_NC}              ${_DIM}Instalación completa (todos los módulos)${_NC}"
    echo "  ${_BG}[2]${_NC}  ${_WH}Solo núcleo${_NC}       ${_DIM}Core + Anthropic Claude (mínimo funcional)${_NC}"
    echo "  ${_BG}[3]${_NC}  ${_WH}Personalizado${_NC}     ${_DIM}Selecciona módulos individualmente${_NC}"
    echo ""
    echo "  ${_BG}[0]${_NC}  ${_RD}Cancelar${_NC}"
    echo ""
    _hr
}

_print_module_menu() {
    echo ""
    _print_center "Selección de módulos" "$_WH"
    echo ""
    _print_center "Escribe los números separados por espacio (ej: 1 3 5)" "$_DIM"
    echo ""
    echo "  ${_BG}[1]${_NC}  Reconocimiento de voz    ${_DIM}SpeechRecognition, pyttsx3, gtts, pyaudio${_NC}"
    echo "  ${_BG}[2]${_NC}  GUI / Bandeja sistema    ${_DIM}PyQt6, animación HUD, chat flotante${_NC}"
    echo "  ${_BG}[3]${_NC}  Google ADK + Claude      ${_DIM}google-adk, litellm (backend adk)${_NC}"
    echo "  ${_BG}[4]${_NC}  Google ADK + Gemini      ${_DIM}google-adk nativo (backend gemini)${_NC}"
    echo "  ${_BG}[5]${_NC}  Ollama (modelos locales) ${_DIM}Sin dependencias Python extra${_NC}"
    echo "  ${_BG}[6]${_NC}  Servidor A2A             ${_DIM}FastAPI, uvicorn (Agent-to-Agent)${_NC}"
    echo "  ${_BG}[7]${_NC}  Soporte MCP              ${_DIM}mcp (Model Context Protocol)${_NC}"
    echo "  ${_BG}[8]${_NC}  Computer Use ★           ${_DIM}google-genai, playwright, pyautogui${_NC}"
    echo "  ${_BG}[9]${_NC}  Extractor de assets      ${_DIM}yt-dlp (icono y audio de bienvenida)${_NC}"
    echo ""
    _hr
    echo ""
    printf "  Módulos a instalar: "
}

# ─── Barra de progreso de instalación ────────────────────────────────────────
_progress_sequence() {
    local groups=("$@")
    local total=${#groups[@]}
    local done=0
    for group in "${groups[@]}"; do
        done=$(( done + 1 ))
        local pct=$(( done * 100 / total ))
        _progress_bar "$(printf '%-20s' "$group")" "$pct"
        _install_group "$group"
        echo ""
    done
}

# ─── Entry point ─────────────────────────────────────────────────────────────
main() {
    _splash

    # Mostrar versión y fecha
    _print_center "v1.1.0  ·  $(date '+%Y-%m-%d')" "$_DIM"
    echo ""

    _check_system

    _info "Preparando entorno virtual..."
    echo ""
    _setup_venv
    echo ""

    # Siempre instalar núcleo
    _progress_bar "core" 0
    _install_group core
    echo ""

    _hr
    _print_menu

    local choice
    read -rp "  Selección [0-3]: " choice
    echo ""

    case "$choice" in
        1)
            _print_center "Instalando todos los módulos…" "$_CY"
            echo ""
            local all_groups=(voice tray adk gemini a2a mcp "computer-use" assets)
            _progress_sequence "${all_groups[@]}"
            ;;
        2)
            _ok "Instalación de núcleo completada"
            ;;
        3)
            _print_module_menu
            local selections
            read -ra selections

            local selected_groups=()
            for sel in "${selections[@]}"; do
                case "$sel" in
                    1) selected_groups+=(voice) ;;
                    2) selected_groups+=(tray) ;;
                    3) selected_groups+=(adk) ;;
                    4) selected_groups+=(gemini) ;;
                    5) selected_groups+=(ollama) ;;
                    6) selected_groups+=(a2a) ;;
                    7) selected_groups+=(mcp) ;;
                    8) selected_groups+=("computer-use") ;;
                    9) selected_groups+=(assets) ;;
                    *) _warn "Opción '$sel' ignorada" ;;
                esac
            done

            if [ ${#selected_groups[@]} -eq 0 ]; then
                _warn "No se seleccionaron módulos adicionales"
            else
                echo ""
                _print_center "Instalando módulos seleccionados…" "$_CY"
                echo ""
                _progress_sequence "${selected_groups[@]}"
            fi
            ;;
        0)
            echo ""
            _warn "Instalación cancelada por el usuario"
            exit 0
            ;;
        *)
            _warn "Opción inválida — se instaló solo el núcleo"
            ;;
    esac

    echo ""
    _setup_env
    echo ""
    _create_launcher
    _print_summary
}

main "$@"
