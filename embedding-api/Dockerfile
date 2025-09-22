# Dockerfile para o serviço embedding-api

# Usa uma imagem base leve do Python 3.10
FROM python:3.10-slim

# Informações de manutenção
LABEL maintainer="moacyr@exemplo.com"

# Evita criação de arquivos .pyc e força saída de logs no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências para o container
COPY requirements.txt .

# Instala as dependências listadas no requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o script principal da aplicação Flask
COPY app.py .

# Copia a pasta do modelo local para dentro do container
# Isso garante que SentenceTransformer("modelo") funcione corretamente
COPY modelo/ modelo/

# Expõe a porta 5000 para acesso externo (ajuste se necessário)
EXPOSE 5000

# Comando que inicia o serviço Flask
CMD ["python", "app.py"]