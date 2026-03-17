FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy telegram module
COPY . ./telegram/

# Shared dependencies: languages and currency service
COPY ../languages/ ./languages/

ENV PYTHONPATH=/app

CMD ["python", "-m", "telegram.bot"]
