FROM python:3.11-slim

WORKDIR /app

# Install system prerequisites (curl and bash for OpenClaw)
RUN apt-get update && apt-get install -y curl bash && rm -rf /var/lib/apt/lists/*

# Install OpenClaw CLI
RUN curl -fsSL https://openclaw.ai/install.sh | bash

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
