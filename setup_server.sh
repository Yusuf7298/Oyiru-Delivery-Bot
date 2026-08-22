#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "   🚀 OYIRU DELIVERY BOT - SERVER INITIAL SETUP (YEGARA)"
echo "=========================================================="

# 1. Update OS Packages
echo "[1/6] Updating system packages..."
if [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git curl
elif [ -x "$(command -v dnf)" ]; then
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip git curl
elif [ -x "$(command -v yum)" ]; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip git curl
fi

# 2. Setup Project Directory
PROJECT_DIR="/var/www/oyiru_bot"
echo "[2/6] Setting up project directory at $PROJECT_DIR..."
sudo mkdir -p $PROJECT_DIR
sudo mkdir -p $PROJECT_DIR/logs
sudo mkdir -p $PROJECT_DIR/uploads

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$CURRENT_DIR" != "$PROJECT_DIR" ]; then
    echo "Copying files from $CURRENT_DIR to $PROJECT_DIR..."
    sudo cp -r $CURRENT_DIR/* $PROJECT_DIR/
fi

cd $PROJECT_DIR

# 3. Create Python Virtual Environment
echo "[3/6] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Environment File Check
echo "[4/6] Checking .env configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️ Created .env from .env.example. Please update .env with your BOT_TOKEN!"
    else
        echo "⚠️ .env file missing! Creating a blank .env template..."
        touch .env
    fi
fi

# 5. Setup Systemd Service
echo "[5/6] Installing systemd service..."
sudo cp oyiru-bot.service /etc/systemd/system/oyiru-bot.service
sudo systemctl daemon-reload
sudo systemctl enable oyiru-bot
sudo systemctl restart oyiru-bot

# 6. Check Service Status
echo "[6/6] Verifying bot service status..."
sleep 2
sudo systemctl status oyiru-bot --no-pager

echo ""
echo "=========================================================="
echo "   🎉 BOT DEPLOYED AND RUNNING SUCCESSFULLY ON YEGARA!"
echo "=========================================================="
echo "• View live logs: sudo journalctl -u oyiru-bot -f"
echo "• Or view file logs: tail -f /var/www/oyiru_bot/logs/bot.log"
echo "• Restart bot: sudo systemctl restart oyiru-bot"
echo "• Stop bot: sudo systemctl stop oyiru-bot"
echo "=========================================================="
