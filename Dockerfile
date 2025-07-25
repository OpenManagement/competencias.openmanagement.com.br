# --- Início do Dockerfile ---
FROM python:3.11-slim

# 1) Dependências do sistema (inclua aqui tudo que seu projeto precisar)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        wkhtmltopdf \
        libxrender1 \
        libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# 2) Definição do diretório de trabalho
WORKDIR /app

# 3) Copia e instala requisitos Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copia todo o restante do seu código
COPY . .

# 5) (opcional, documentacional) expõe a porta
EXPOSE 8080

# 6) Shell form do CMD para expandir $PORT
CMD sh -lc "exec gunicorn app:app --bind 0.0.0.0:${PORT:-8080}"
# --- Fim do Dockerfile ---
