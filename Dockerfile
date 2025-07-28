FROM python:3.11-slim

# Instalar dependências do sistema (inclui o wkhtmltopdf e libs gráficas necessárias)
RUN apt-get update && \
    apt-get install -y wkhtmltopdf build-essential libssl-dev libffi-dev \
    python3-dev libxrender1 libfontconfig1 libxext6 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código do app
COPY . .

# Configurar a porta padrão (será sobrescrita pelo Railway)
ENV PORT=9000

# Comando padrão para iniciar o app
CMD ["python", "app.py"]