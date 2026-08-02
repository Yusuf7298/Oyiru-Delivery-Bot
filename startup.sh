#!/bin/bash
echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

# Clean up broken virtual environment if python is not functional
if [ -d "/home/site/wwwroot/antenv" ]; then
    if ! /home/site/wwwroot/antenv/bin/python --version >/dev/null 2>&1; then
        echo "Removing broken virtual environment..."
        rm -rf /home/site/wwwroot/antenv
    fi
fi

# Create virtual environment if missing
if [ ! -d "/home/site/wwwroot/antenv" ]; then
    echo "Creating fresh virtual environment..."
    python3 -m venv /home/site/wwwroot/antenv
fi

# Install dependencies ONLY if missing to avoid startup timeout
if ! /home/site/wwwroot/antenv/bin/python -c "import aiogram" >/dev/null 2>&1; then
    echo "Installing dependencies..."
    /home/site/wwwroot/antenv/bin/pip install -r requirements.txt
else
    echo "Dependencies already installed. Skipping pip install for instant boot."
fi

# Run database setup
echo "Running database setup..."
/home/site/wwwroot/antenv/bin/python -m alembic upgrade head || /home/site/wwwroot/antenv/bin/python create_tables.py || echo "DB setup warning"

# Start app
echo "Starting app.py..."
exec /home/site/wwwroot/antenv/bin/python app.py
