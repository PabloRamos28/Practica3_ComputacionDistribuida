FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY games.json ./games.json

EXPOSE 5000

# Crea tablas, carga el catálogo inicial (solo la primera vez) y arranca la API.
CMD ["sh", "-c", "flask --app backend.app init-db && (python -m backend.seed_games || true) && flask --app backend.app run --host=0.0.0.0 --port=5000"]
