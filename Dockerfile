# Imagem base enxuta
FROM python:3.12-slim

# Desabilita buffers + não guarda cache do pip
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependências mínimas de build (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# ───── etapa de dependências ────────────────────────────────
WORKDIR /app

# requirements.txt está dentro de backend/
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# ───── copia o código-fonte ─────────────────────────────────
COPY backend ./backend

# Porta exposta
EXPOSE 8000

# Comando default: roda a API que está em backend/main.py
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
