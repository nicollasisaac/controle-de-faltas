# Imagem base enxuta
FROM python:3.12-slim

# Evita prompts & mantém logs visíveis
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instala dependências do sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc netcat && \
    rm -rf /var/lib/apt/lists/*

# Copia apenas o requirements e instala (camada de cache)
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante do código
COPY . .

# Porta exposta no contêiner
EXPOSE 8000

# Comando padrão (Render detecta automaticamente)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
