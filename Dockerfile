# 1) Imagem base leve
FROM python:3.11-slim

# 2) Instala dependências do sistema
#    Ajuste aqui caso seu Dockerfile original tenha outras libs além de wkhtmltopdf
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        wkhtmltopdf \
        libxrender1 \
        libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# 3) Cria e define diretório de trabalho
WORKDIR /app

# 4) Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copia o restante do código
COPY . .

# 6) Porta exposta (documentação; Railway ignora mas é bom manter)
EXPOSE 8080

# 7) Start em shell form para expandir $PORT corretamente
CMD exec gunicorn app:app --bind 0.0.0.0:${PORT:-8080}