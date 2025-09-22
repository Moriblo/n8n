# Dockerfile para o serviço avalsimilar
FROM python:3.10-slim

LABEL maintainer="blondet.mr@gmail.com"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o script principal
COPY avalsimilar.py .

# Expõe a porta usada pelo Flask
EXPOSE 5000

# Executa o serviço
CMD ["python", "avalsimilar.py"]
