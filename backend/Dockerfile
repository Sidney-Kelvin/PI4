FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# PyTorch somente CPU (evita baixar ~2 GB de bibliotecas CUDA desnecessárias)
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

# Aplica as migrations (fonte oficial da estrutura do banco) e inicia a API.
# O docker-compose só inicia este container depois que o PostgreSQL está saudável.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080"]
