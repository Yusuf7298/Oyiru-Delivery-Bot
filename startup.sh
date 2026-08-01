#!/bin/bash
set -e

echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

PYTHON=$(which python3 || which python)

echo "Python interpreter: $PYTHON"

# Run database migrations
echo "Running database migrations..."
$PYTHON -m alembic upgrade head || echo "Alembic migration warning/skipped"

# Start the bot directly
echo "Starting app.py..."
exec $PYTHON app.py
