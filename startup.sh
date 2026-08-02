#!/bin/bash
echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

# Ensure virtual environment exists and is clear of broken files
if [ ! -f "/home/site/wwwroot/antenv/bin/python" ]; then
    echo "Creating virtual environment at /home/site/wwwroot/antenv..."
    python3 -m venv --clear /home/site/wwwroot/antenv || true
fi

# Set Python and Pip executables
if [ -f "/home/site/wwwroot/antenv/bin/python" ]; then
    PYTHON="/home/site/wwwroot/antenv/bin/python"
    PIP="/home/site/wwwroot/antenv/bin/pip"
else
    PYTHON=$(which python3 || which python)
    PIP=$(which pip3 || which pip)
fi

echo "Using Python: $PYTHON"
echo "Using Pip: $PIP"

# Install dependencies if aiogram is missing
if ! $PYTHON -c "import aiogram" >/dev/null 2>&1; then
    echo "Installing dependencies..."
    $PIP install --upgrade pip --quiet || true
    $PIP install -r requirements.txt
else
    echo "Dependencies verified OK."
fi

# Run database setup
echo "Running database setup..."
$PYTHON -m alembic upgrade head || $PYTHON create_tables.py || echo "DB setup warning"

# Start app
echo "Starting app.py..."
exec $PYTHON app.py
