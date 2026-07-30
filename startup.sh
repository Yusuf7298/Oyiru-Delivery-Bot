#!/bin/bash
set -e

echo "=== Oyiru Delivery Bot Startup ==="

# Install dependencies if not already installed
if [ -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r /home/site/wwwroot/requirements.txt --quiet
fi

# Change to app directory
cd /home/site/wwwroot

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Start the bot
echo "Starting bot..."
python app.py
