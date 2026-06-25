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
PYENV_PYTHON="$HOME/.pyenv/versions/3.11.9/bin/python3.11"

# The Ubuntu release on this host ships Python 3.14 by default, which is too
# new for pinned deps (greenlet/pydantic-core/psycopg2-binary lack 3.14 wheels),
# and deadsnakes does not publish 3.11 packages for this release. Python 3.11
# is built via pyenv instead; deploy scripts run over a non-interactive SSH
# session that does not source ~/.bashrc, so the pyenv shim PATH is unavailable
# and the binary must be referenced by its full path.
if command -v python3.11 &> /dev/null; then
    PYTHON_BIN="python3.11"
elif [ -x "$PYENV_PYTHON" ]; then
    PYTHON_BIN="$PYENV_PYTHON"
else
    echo "ERROR: python3.11 not found (checked PATH and $PYENV_PYTHON)."
    echo "Install it with: curl https://pyenv.run | bash && ~/.pyenv/bin/pyenv install 3.11.9"
    exit 1
fi

# Recreate the venv if it was built with a different Python version
# (e.g. left over from manual troubleshooting with the system python3)
if [ -d "$VENV_DIR" ]; then
    EXISTING_VERSION="$("$VENV_DIR/bin/python" --version 2>&1 | awk '{print $2}')"
    if [[ "$EXISTING_VERSION" != 3.11.* ]]; then
        echo "Existing $VENV_DIR uses Python $EXISTING_VERSION, expected 3.11.x. Recreating..."
        rm -rf "$VENV_DIR"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
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
