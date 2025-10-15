# ===========================
# 📦 db_service Dockerfile
# ===========================
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pymysql

# Copy app files
COPY . .

# Expose port
EXPOSE 8002

# Wait for MySQL to be ready (optional: add healthcheck in Compose)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
