#!/bin/bash
# run_web_prod.sh
# Compila el frontend de Vue y levanta el servidor FastAPI sirviéndolo en producción.

# Activar entorno virtual de python si existe
if [ -f "jarvis/.venv/bin/activate" ]; then
    source jarvis/.venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "📦 Compilando Frontend Vite (Vue)..."
cd www
pnpm install
pnpm run build
cd ..

echo "🚀 Iniciando Backend FastAPI en modo producción (Port 8000)..."
echo "🌐 Abre http://127.0.0.1:8000 en tu navegador"
python3 -m jarvis --serve-web
