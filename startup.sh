#!/bin/bash
echo "=== Oyiru Delivery Bot Startup ==="

cd /home/site/wwwroot

# Activate virtual environment if available
if [ -f "/home/site/wwwroot/antenv/bin/activate" ]; then
    source /home/site/wwwroot/antenv/bin/activate
fi

# Determine Python binary path
if [ -f "/home/site/wwwroot/antenv/bin/python3" ]; then
    PYTHON="/home/site/wwwroot/antenv/bin/python3"
elif [ -f "/home/site/wwwroot/antenv/bin/python" ]; then
    PYTHON="/home/site/wwwroot/antenv/bin/python"
else
    PYTHON=$(which python3 || which python)
fi

echo "Selected Python: $PYTHON"

# Install dependencies using antenv pip
if [ -f "/home/site/wwwroot/antenv/bin/pip3" ]; then
    echo "Installing requirements via antenv pip3..."
    /home/site/wwwroot/antenv/bin/pip3 install -r requirements.txt
elif [ -f "/home/site/wwwroot/antenv/bin/pip" ]; then
    echo "Installing requirements via antenv pip..."
    /home/site/wwwroot/antenv/bin/pip install -r requirements.txt
fi

# Run database setup
echo "Running database setup..."
$PYTHON -m alembic upgrade head || $PYTHON create_tables.py || echo "DB setup skipped"

# Start app
echo "Starting app.py..."
exec $PYTHON app.py
