#!/bin/bash
set -e

echo "=== Oyiru Delivery Bot Startup ==="

# Change to app directory
cd /home/site/wwwroot

# Use python3 (Linux) with fallback
PYTHON=$(which python3 || which python)
PIP=$(which pip3 || which pip)

echo "Python: $PYTHON"
echo "Pip: $PIP"

# Install dependencies
echo "Installing dependencies..."
$PIP install -r requirements.txt --quiet

# Run database migrations
echo "Running database migrations..."
$PYTHON -m alembic upgrade head

# Start the bot
echo "Starting bot..."
$PYTHON app.py
