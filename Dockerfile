# syntax=docker/dockerfile:1

# Usa la versión de Python que necesitas
ARG PYTHON_VERSION=3.13.2
FROM python:${PYTHON_VERSION}-slim

# Etiqueta informativa
LABEL fly_launch_runtime="flask"

# Establece el directorio de trabajo dentro de la imagen
WORKDIR /code

# Instala primero las dependencias de Python (aprovecha mejor la caché de Docker)
COPY requirements.txt requirements.txt
# Usamos --no-cache-dir para mantener la imagen un poco más limpia
RUN pip3 install --no-cache-dir -r requirements.txt

# --- Añadir Instalación de Node.js y Build de Tailwind CSS ---

# Instalar dependencias necesarias para descargar Node.js (curl) y certificados
RUN apt-get update && apt-get install -y curl ca-certificates && \
    # Descargar e instalar la versión LTS (Estable a Largo Plazo) de Node.js usando NodeSource
    # Puedes cambiar 'lts.x' por una versión mayor específica si lo prefieres, ej: '20.x'
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    # Limpiar caché de apt para reducir tamaño de imagen
    rm -rf /var/lib/apt/lists/*

# Copiar TODO el código de tu aplicación (backend, static, app.py, tailwind.config.js, etc.)
# Hacemos esto DESPUÉS de instalar dependencias para optimizar caché si solo cambia el código
COPY . .

# (Opcional) Verificar versión de Node/npm para logs de build
RUN node -v
RUN npm -v

# Ejecutar el build de Tailwind CSS para producción
# Las rutas son relativas al WORKDIR (/code)
# Asegura que el directorio de salida exista
RUN mkdir -p /code/backend/static/css
RUN npx tailwindcss -i ./backend/static/src/input.css -o ./backend/static/css/output.css --minify

# --- Fin Build de Tailwind CSS ---


# Puerto que expone Gunicorn (Fly.io lo mapeará a 80/443 externamente)
EXPOSE 8080


# --- Comando de Inicio CORREGIDO para Producción con Gunicorn ---
# Asume que tu archivo principal se llama app.py y la instancia Flask se llama 'app'
# Se enlaza al puerto interno 8080 (Fly lo gestiona)
# Empezamos con 1 worker, puedes ajustar '--workers' más adelante si es necesario
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "app:app"]