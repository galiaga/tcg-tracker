# syntax=docker/dockerfile:1

# --- Base Stage ---
# Common setup for both web and cron images
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim as base

WORKDIR /code

# Prevent python from writing pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Web App Builder Stage ---
# This stage builds the full web application, including Node.js and Tailwind
FROM base as web-builder

ARG GIT_SHA="unknown"
ENV APP_VERSION=${GIT_SHA}

LABEL fly_launch_runtime="flask"

# Install Python dependencies for the web app
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Node.js and npm
RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Node dependencies (includes tailwindcss)
COPY package*.json ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build Tailwind CSS for production
RUN mkdir -p /code/backend/static/css
RUN npx tailwindcss -i ./backend/static/src/input.css -o ./backend/static/css/output.css --minify

# --- Cron Job Builder Stage ---
# This stage builds a minimal image with only the scripts and their dependencies
FROM base as cron-builder

# Copy and install only the cron job's Python dependencies
COPY cron-requirements.txt .
RUN pip3 install --no-cache-dir -r cron-requirements.txt

# Copy only the scripts needed for the cron job
COPY backend/scripts/ ./backend/scripts/

# --- Final Web App Image ---
# This is the default target that will be used for your 'web' process
FROM web-builder as release
EXPOSE 8080
# The command to run the web server will be in fly.toml

# --- Final Cron Job Image ---
# This is a named stage that we will reference from fly.toml
FROM cron-builder as cron_release
# Set the default command for this image
CMD ["python", "backend/scripts/run_updates.py"]