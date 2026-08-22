# 🚀 Deployment Guide: Oyiru Delivery Bot on Yegara Host (SSH)

This step-by-step guide explains how to deploy and run **Oyiru Delivery Bot** 24/7 on a **Yegara Host Linux VPS** using SSH.

---

## 📋 Prerequisites
1. **Yegara Host Linux VPS credentials** (IP Address, SSH Port, Username e.g. `root`, Password or SSH Key).
2. **SSH Client** (Command Prompt / PowerShell on Windows, Terminal on macOS/Linux, or PuTTY).
3. **MongoDB Connection URL** (MongoDB Atlas or self-hosted).
4. **Telegram Bot Token** from [@BotFather](https://t.me/botfather).

---

## 🛠️ Step 1: Connect to your Yegara VPS via SSH

Open your Terminal or PowerShell on your computer and run:

```bash
ssh root@YOUR_YEGARA_SERVER_IP
```
*(Enter your server password when prompted).*

---

## 🛠️ Step 2: Clone or Upload the Bot Code to the Server

### Option A: Via Git (Recommended)
If your code is on GitHub / GitLab:
```bash
cd /var/www
git clone https://github.com/Yusuf7298/Oyiru-Delivery-Bot.git oyiru_bot
cd oyiru_bot
```

### Option B: Via SCP / SFTP (from your local PC)
From your local Windows command prompt:
```bash
scp -r "c:\Users\Lenovo\OneDrive\Desktop\Oyiru Delivery Bot" root@YOUR_YEGARA_SERVER_IP:/var/www/oyiru_bot
```

---

## 🛠️ Step 3: Run the Automated Setup Script

On the server (inside `/var/www/oyiru_bot`):

```bash
cd /var/www/oyiru_bot
chmod +x setup_server.sh deploy.sh
bash setup_server.sh
```

This script will automatically:
1. Install Python 3, `pip`, `venv`, and system dependencies.
2. Create directories for logs (`logs/`) and user upload storage (`uploads/`).
3. Set up the Python virtual environment (`venv`) and install all packages in `requirements.txt`.
4. Install and enable the `oyiru-bot.service` systemd daemon so the bot starts automatically on server boot and auto-restarts if it ever crashes.

---

## 🛠️ Step 4: Configure Production Environment (`.env`)

Edit your `.env` file on the server:

```bash
nano /var/www/oyiru_bot/.env
```

Ensure your credentials are set:
```env
BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
DATABASE_URL=mongodb+srv://...
MONGODB_DB_NAME=oyiru_delivery_bot
ADMIN_ID=8223004316
SUPER_ADMIN_IDS=7269164159,8223004316
```

Save and exit in nano: Press `Ctrl + O`, then `Enter`, then `Ctrl + X`.

Restart the bot to apply the `.env` changes:
```bash
sudo systemctl restart oyiru-bot
```

---

## 📊 Step 5: Verify & Monitor Your Bot

### Check Bot Status:
```bash
sudo systemctl status oyiru-bot
```

### View Live Real-Time Logs:
```bash
sudo journalctl -u oyiru-bot -f
```
*or*
```bash
tail -f /var/www/oyiru_bot/logs/bot.log
```

---

## 🔄 How to Update the Bot in the Future

Whenever you make changes to your codebase:

```bash
cd /var/www/oyiru_bot
bash deploy.sh
```

---

## 🛡️ Useful Management Commands

| Action | Command |
| :--- | :--- |
| **Check Status** | `sudo systemctl status oyiru-bot` |
| **Restart Bot** | `sudo systemctl restart oyiru-bot` |
| **Stop Bot** | `sudo systemctl stop oyiru-bot` |
| **Start Bot** | `sudo systemctl start oyiru-bot` |
| **Live Logs** | `sudo journalctl -u oyiru-bot -f` |
