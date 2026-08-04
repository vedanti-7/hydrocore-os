# ---- development stage ----
FROM python:3.12-slim AS development

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- production stage (used later) ----
FROM python:3.12-slim AS production

WORKDIR /app
RUN useradd --create-home hydrocore
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
USER hydrocore

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
