FROM python:3.12-slim

WORKDIR /app

COPY app/backend/ ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY app/languages/ ./backend/languages/

WORKDIR /app/backend

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
