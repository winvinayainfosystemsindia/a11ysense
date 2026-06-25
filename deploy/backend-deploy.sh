#!/bin/bash
set -e

ENV=$1
if [[ -z "$ENV" ]]; then
  echo "Usage: ./backend-deploy.sh [dev|qa|main]"
  exit 1
fi

if [[ "$ENV" != "dev" && "$ENV" != "qa" && "$ENV" != "main" && "$ENV" != "prod" ]]; then
  echo "Invalid environment: $ENV. Expected one of: dev, qa, main, prod"
  exit 1
fi

# Determine project root dynamically from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
echo "Deploying Backend for $ENV environment in $PROJECT_ROOT..."

cd "$PROJECT_ROOT"

# 1. Load environment variables
if [ -f ".env.$ENV" ]; then
    cp .env.$ENV .env
    echo "Environment file .env.$ENV copied to .env"
fi

# 2. Setup/Activate Virtual Environment matching ecosys.config.js
PM2_ENV=$ENV
if [[ "$ENV" == "main" ]]; then
  PM2_ENV="prod"
fi
VENV_DIR="venv-$PM2_ENV"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 3. Install dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt --quiet

# 4. Restart services via PM2 using ecosys.config.js
echo "Restarting services via PM2 using ecosys.config.js..."
pm2 stop "$PM2_ENV-gateway" "$PM2_ENV-agent" "$PM2_ENV-reporting" "$PM2_ENV-crawler" "$PM2_ENV-analyzer" "$PM2_ENV-llm" --quiet || true
pm2 delete "$PM2_ENV-gateway" "$PM2_ENV-agent" "$PM2_ENV-reporting" "$PM2_ENV-crawler" "$PM2_ENV-analyzer" "$PM2_ENV-llm" --quiet || true

pm2 start ecosys.config.js --only "$PM2_ENV-gateway,$PM2_ENV-agent,$PM2_ENV-reporting,$PM2_ENV-crawler,$PM2_ENV-analyzer,$PM2_ENV-llm"

echo "Backend deployment to $ENV completed successfully."
