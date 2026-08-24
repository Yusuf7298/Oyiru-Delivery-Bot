# 🏨 Oyirubot Telegram Bot

Welcome to **Oyirubot** — a modern, multi-lingual Telegram Bot for hotel food & item delivery, multi-role user management, and order tracking.

---

## 🌟 Key Features

- 🌐 **Native 3-Language Support**:
  - 🇬🇧 **English**
  - 🇪🇹 **አማርኛ (Amharic)**
  - 🇪🇹 **Afaan Oromoo**
- 👥 **Multi-Role System**:
  - **Customers**: Select hotel, browse categories/products, upload order lists, track active orders, report returns.
  - **Store Managers (Hotels)**: View new orders, mark order progress (Submitted ➡️ Preparing ➡️ Packed ➡️ Out for Delivery).
  - **Delivery Partners**: Receive delivery assignments, accept/reject deliveries, update status.
  - **Admins**: Approve registrations, assign drivers, manage hotels/categories/products, view analytics & broadcasts.

---

## 🚀 Beginner Quick Start Guide

Follow these simple steps to run the bot on your computer:

### Step 1: Install Python
Make sure you have **Python 3.10+** installed on your system.
You can check by running in your terminal:
```bash
python --version
```

### Step 2: Install Required Libraries
Open PowerShell or Terminal in the project folder and run:
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables (`.env`)
1. Duplicate `.env.example` and rename it to `.env`.
2. Get your Bot Token from Telegram [@BotFather](https://t.me/BotFather).
3. Open `.env` and set your values:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
DATABASE_URL=mongodb://localhost:27017/oyiru_db
SUPER_ADMIN_IDS=your_telegram_user_id
```

### Step 4: Seed Initial Sample Data (Optional)
To pre-populate sample hotels, categories, and products:
```bash
python scripts/seed_hotels.py
python scripts/seed_categories.py
python scripts/seed_products.py
```

### Step 5: Start the Bot! 🎉
Run the main application entrypoint:
```bash
python app.py
```

You should see:
```text
Logging initialized successfully.
Health check web server running on port 8000
Bot started — polling
```

Now open Telegram, search for your bot, and send `/start`!

---

## 🌐 How to Change Language in Bot

Users can switch languages anytime by sending `/language` or tapping the **🌐 Language** button in the main menu:
1. 🇬🇧 **English**
2. 🇪🇹 **አማርኛ (Amharic)**
3. 🇪🇹 **Afaan Oromoo**

---

## 🛠️ Project Structure

```text
Oyirubot/
├── app.py                 # Main bot launcher & polling loop
├── config/                # Environment & Logging configuration
├── database/              # Database models & repositories
├── handlers/              # Role-specific Telegram message handlers
│   ├── admin/             # Admin handlers
│   ├── customer/          # Customer handlers (Order, View, Returns)
│   ├── delivery/          # Delivery partner handlers
│   ├── hotel/             # Store Manager handlers
│   └── common/            # Shared handlers (Language, Cancel, Fallback)
├── keyboards/             # Localized Telegram Reply & Inline keyboards
├── middlewares/           # Auth, Database, Logging, Language middlewares
├── translations/          # Translation JSON files (en.json, am.json, om.json)
├── scripts/               # Database seeding scripts
└── utils/                 # i18n translation engine & helper functions
```

---

## ❓ Frequently Asked Questions & Troubleshooting

### Q: Why did the bot fail with "Missing required environment variables"?
**A**: Make sure you created a `.env` file in the project folder containing `BOT_TOKEN` and `DATABASE_URL`.

### Q: How do I become an Admin?
**A**: Add your Telegram User ID (get it from [@userinfobot](https://t.me/userinfobot)) to `SUPER_ADMIN_IDS` in your `.env` file.

### Q: How do I add new languages?
**A**: Create a new JSON file in `translations/` (e.g. `fr.json`) and register it in `utils/i18n.py`.

