#!/bin/bash
echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

# Remove broken virtualenv if interpreter is invalid
if [ -d "/home/site/wwwroot/antenv" ]; then
    if ! /home/site/wwwroot/antenv/bin/python --version >/dev/null 2>&1; then
        echo "Detected broken antenv virtualenv. Rebuilding..."
        rm -rf /home/site/wwwroot/antenv
    fi
fi

# Create fresh virtual environment if missing
if [ ! -d "/home/site/wwwroot/antenv" ]; then
    echo "Creating fresh virtual environment at /home/site/wwwroot/antenv..."
    python3 -m venv /home/site/wwwroot/antenv || virtualenv /home/site/wwwroot/antenv || true
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

# Install dependencies into virtualenv
echo "Installing dependencies from requirements.txt..."
$PIP install --upgrade pip --quiet || true
$PIP install -r requirements.txt

# Run database setup
echo "Running database setup..."
$PYTHON -m alembic upgrade head || $PYTHON create_tables.py || echo "DB setup skipped"

# Start app
echo "Starting app.py..."
exec $PYTHON app.py
