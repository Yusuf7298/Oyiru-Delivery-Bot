#!/bin/bash
echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

# Ensure virtual environment exists using --without-pip for Debian/Ubuntu compatibility
if [ ! -f "/home/site/wwwroot/antenv/bin/python" ]; then
    echo "Creating virtual environment at /home/site/wwwroot/antenv..."
    python3 -m venv --without-pip /home/site/wwwroot/antenv || true
fi

# Ensure pip is installed inside antenv if missing
if [ ! -f "/home/site/wwwroot/antenv/bin/pip" ]; then
    echo "Installing pip into virtual environment..."
    curl -sS https://bootstrap.pypa.io/pip/3.9/get-pip.py | /home/site/wwwroot/antenv/bin/python3 || curl -sS https://bootstrap.pypa.io/get-pip.py | /home/site/wwwroot/antenv/bin/python3 || true
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

# Run database setup & sync
echo "Running database setup..."
$PYTHON scripts/sync_db_schema.py || echo "DB setup warning"

# Start app
echo "Starting app.py..."
exec $PYTHON app.py
