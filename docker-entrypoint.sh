#!/bin/bash
set -e

# Configurar permisos para audio/X11 si es necesario.
# (En un entorno de contenedor Docker, root es el usuario por defecto).

# Si existe un volumen .env y está vacío o no existe, copiamos el .env.example
if [ ! -f "jarvis/.env" ]; then
    if [ -f "jarvis/.env.example" ]; then
        echo "[Entrypoint] jarvis/.env no encontrado. Copiando jarvis/.env.example..."
        cp jarvis/.env.example jarvis/.env
    else
        echo "[Entrypoint] Advertencia: jarvis/.env no existe y no hay .env.example."
    fi
fi

# Iniciar la aplicación
echo "[Entrypoint] Iniciando Palmiche J.A.R.V.I.S..."
exec "$@"
