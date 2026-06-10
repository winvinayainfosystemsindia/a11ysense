#!/bin/bash
set -e
ENV=$1
if [[ -z "$ENV" ]]; then
  echo "Usage: ./frontend-deploy.sh [dev|qa|main]"
  exit 1
fi

if [[ "$ENV" != "dev" && "$ENV" != "qa" && "$ENV" != "main" && "$ENV" != "prod" ]]; then
  echo "Invalid environment: $ENV. Expected one of: dev, qa, main, prod"
  exit 1
fi
PROJECT_ROOT="/var/www/a11ysense-ai/$ENV"
echo "Deploying Frontend for $ENV environment in $PROJECT_ROOT..."

cd $PROJECT_ROOT/frontend

# 1. Install dependencies
echo "Installing NPM dependencies..."
npm install --quiet

# 2. Build for production
echo "Building frontend for $ENV..."
VITE_APP_ENV=$ENV npm run build --quiet

echo "Frontend build for $ENV completed successfully."
