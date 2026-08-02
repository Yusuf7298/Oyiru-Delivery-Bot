#!/bin/bash
echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

# Find Python binary with venv/pip support
for p in \
    /home/site/wwwroot/antenv/bin/python \
    /antenv/bin/python \
    /opt/python/3.11.15/bin/python3 \
    /opt/python/3.11/bin/python3 \
    /opt/python/latest/bin/python3 \
    /usr/local/bin/python3 \
    $(which python3) \
    $(which python)
do
    if [ -x "$p" ]; then
        PYTHON="$p"
        break
    fi
done

echo "Selected base Python: $PYTHON"

# Create antenv virtual environment if it doesn't exist
if [ ! -f "/home/site/wwwroot/antenv/bin/python" ]; then
    echo "Creating virtual environment at /home/site/wwwroot/antenv..."
    $PYTHON -m venv /home/site/wwwroot/antenv || python3 -m venv /home/site/wwwroot/antenv || true
fi

# Use virtual environment Python if available
if [ -f "/home/site/wwwroot/antenv/bin/python" ]; then
    PYTHON="/home/site/wwwroot/antenv/bin/python"
fi

echo "Virtualenv Python: $PYTHON"

# Ensure dependencies are installed in virtualenv
if ! $PYTHON -c "import aiogram" 2>/dev/null; then
    echo "aiogram not found. Installing dependencies into virtual environment..."
    $PYTHON -m pip install --upgrade pip --quiet || true
    $PYTHON -m pip install -r requirements.txt
else
    echo "Dependencies verified OK."
fi

# Run database setup
echo "Running database setup..."
$PYTHON -m alembic upgrade head || $PYTHON create_tables.py || echo "DB setup skipped"

# Start the bot
echo "Starting app.py..."
exec $PYTHON app.py
