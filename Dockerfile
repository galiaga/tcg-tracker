# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13.2
FROM python:${PYTHON_VERSION}-slim

ARG GIT_SHA="unknown"
ENV APP_VERSION=${GIT_SHA}

LABEL fly_launch_runtime="flask"

WORKDIR /code

# Instalar dependencias Python
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Instalar Node.js y npm
RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Node (incluye tailwindcss)
COPY package*.json ./
RUN npm install

# Copiar el resto del código de la aplicación
COPY . .

# Construir Tailwind CSS para producción
RUN mkdir -p /code/backend/static/css
RUN npx tailwindcss -i ./backend/static/src/input.css -o ./backend/static/css/output.css --minify

# Exponer puerto
EXPOSE 8080

# Comando para ejecutar el servidor de producción
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "app:app"]