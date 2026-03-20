FROM python:3.12-slim

WORKDIR /app

COPY app/telegram/ ./telegram/
RUN pip install --no-cache-dir -r telegram/requirements.txt

# Shared dependencies: languages and currency service
COPY app/languages/ ./languages/

ENV PYTHONPATH=/app

CMD ["python", "-m", "telegram.bot"]
