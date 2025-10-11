# ---- Stage 1: build del frontend (Vite) ----
FROM node:20-alpine AS fe
WORKDIR /fe
COPY frontend/ ./
RUN npm ci && npm run build

# ---- Stage 2 (Python) ----
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# libs del sistema que sí necesitas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY backend/ ./backend/
COPY backend/requirements.txt ./backend/requirements.txt

# 👇 clave: extra index con wheels precompiladas de llama-cpp-python
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir \
      --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
      -r backend/requirements.txt

# copiar build del FE si lo usas
COPY --from=fe /fe/dist ./backend/frontend_dist

ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn","backend.app:app","--host","0.0.0.0","--port","8000"]
