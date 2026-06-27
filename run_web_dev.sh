#!/bin/bash
# run_web_dev.sh
# Inicia el servidor backend de FastAPI y el frontend de Vue en modo desarrollo.

# Activar entorno virtual de python si existe
if [ -f "jarvis/.venv/bin/activate" ]; then
    source jarvis/.venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "🚀 Iniciando Backend FastAPI (Port 8000)..."
python3 -m jarvis --serve-web &
BACKEND_PID=$!

echo "🚀 Iniciando Frontend Vite (Vue) en modo desarrollo..."
cd www
pnpm install
pnpm run dev &
FRONTEND_PID=$!

# Atrapar Ctrl+C para cerrar ambos procesos limipamente
trap "echo 'Cerrando servidores...'; kill $BACKEND_PID $FRONTEND_PID" SIGINT SIGTERM

# Esperar a que ambos procesos terminen
wait
