#!/bin/bash
echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

# Find virtual environment Python or system Python
if [ -f "/home/site/wwwroot/antenv/bin/python" ]; then
    PYTHON="/home/site/wwwroot/antenv/bin/python"
elif [ -f "/antenv/bin/python" ]; then
    PYTHON="/antenv/bin/python"
elif [ -f "/opt/startup/antenv/bin/python" ]; then
    PYTHON="/opt/startup/antenv/bin/python"
else
    PYTHON=$(which python3 || which python)
fi

echo "Selected Python interpreter: $PYTHON"

# Ensure dependencies are installed
if ! $PYTHON -c "import aiogram" 2>/dev/null; then
    echo "aiogram not found. Installing dependencies from requirements.txt..."
    $PYTHON -m pip install --no-cache-dir -r requirements.txt
else
    echo "Dependencies verified OK."
fi

# Run database migrations / table creation
echo "Running database setup..."
$PYTHON -m alembic upgrade head || $PYTHON create_tables.py || echo "DB setup skipped"

# Start the bot
echo "Starting app.py..."
exec $PYTHON app.py
