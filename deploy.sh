#!/usr/bin/env bash
set -e

PROJECT_DIR="/var/www/oyiru_bot"
cd $PROJECT_DIR

echo "=========================================================="
echo "   🔄 UPDATING OYIRUBOT"
echo "=========================================================="

# 1. Pull latest code if git repo
if [ -d ".git" ]; then
    echo "[1/3] Pulling latest git changes..."
    git pull origin main || git pull origin master || true
fi

# 2. Update Python dependencies
echo "[2/3] Checking dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# 3. Restart bot service
echo "[3/3] Restarting oyiru-bot service..."
sudo systemctl restart oyiru-bot
sleep 2
sudo systemctl status oyiru-bot --no-pager

echo ""
echo "=========================================================="
echo "   ✅ UPDATE COMPLETE & SERVICE RUNNING!"
echo "=========================================================="
