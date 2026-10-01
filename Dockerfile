# Base Python image with Playwright browser support
FROM mcr.microsoft.com/playwright/python:v1.41.2-jammy

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Install Playwright browsers (chromium)
RUN playwright install chromium

# Copy codebase
COPY backend /app/backend
COPY common /app/common

# Create storage directory
RUN mkdir -p /app/storage/diskcache /app/storage/reports

EXPOSE 8000

ENV PYTHONPATH=/app/backend:/app
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
