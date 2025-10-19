# ===========================
# 📦 generate_service Dockerfile
# ===========================
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt httpx

# Copy all service files
COPY . .

# Set environment variable for OpenAI key (can be passed in docker-compose)
ENV OPENAI_API_KEY=""

# Expose port
EXPOSE 8003

# Start FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
