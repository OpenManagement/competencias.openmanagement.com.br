FROM python:3.11-slim

# Instalar dependências do sistema necessárias para o wkhtmltopdf funcionar corretamente
RUN apt-get update && \
    apt-get install -y \
    wget \
    xfonts-base \
    libjpeg62-turbo \
    libxrender1 \
    libxtst6 \
    libxext6 \
    libfontconfig1 \
    wkhtmltopdf && \
    apt-get clean

# Define o diretório de trabalho no container
WORKDIR /app

# Copia todos os arquivos do projeto para dentro do container
COPY . /app

# Instala os pacotes Python necessários com base no requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pelo Gunicorn (porta padrão da Railway)
EXPOSE 8080

# Comando para iniciar o Gunicorn com Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
