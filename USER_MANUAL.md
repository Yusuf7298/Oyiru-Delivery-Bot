# 📖 Oyirubot — Comprehensive User Manual & Operations Guide

Welcome to **Oyirubot**, the automated order management and delivery dispatch system for hotels, restaurants, and fresh food supply chains.

---

## 📑 Table of Contents
1. [🌐 General Getting Started & Language Selection](#1-getting-started--language-selection)
2. [🏨 Hotel Administrator Guide](#2-hotel-administrator-guide)
3. [👤 Hotel Ordering Staff (Customer) Guide](#3-hotel-ordering-staff-customer-guide)
4. [🚚 Delivery Partner Guide (Drivers & Couriers)](#4-delivery-partner-guide)
5. [👑 Admin & Super Admin Guide (Operations & Management)](#5-admin--super-admin-guide)
6. [📢 Telegram Channel & Notification Matrix](#6-channel--group-notifications)

---

## 1. Getting Started & Language Selection

### Starting the Bot
1. Open Telegram and search for **@Oyirubot** (or open your organization's bot link).
2. Tap **Start** or type /start.

### Language Selection
The bot supports 3 languages:
- 🇬🇧 **English**
- 🇪🇹 **አማርኛ (Amharic)**
- 🇪🇹 **Afaan Oromoo**

You can switch your language at any time by tapping **🌐 Language** from the main menu.

---

## 2. Hotel Administrator Guide

Hotel Administrators oversee branch ordering, manage authorized ordering staff, track fulfillment, and export branch data.

### 2.1 Initial Hotel Registration (Claiming a Hotel)
1. When starting the bot for the first time, select your preferred language.
2. The bot displays the list of **unclaimed hotels**.
3. Select your hotel to register as its **Hotel Administrator**.
4. Enter your **Full Name** and **Phone Number**.
5. Once submitted, your registration is reviewed and activated by the Super Administrator.
6. **Security Note**: Once you register for your hotel, it is claimed and permanently removed from the public registration list so unauthorized users cannot select it.

---

### 2.2 Managing Ordering Staff (👥 My Staff)
Hotel Admins have exclusive control over who can place orders for their hotel:
1. Tap **👥 My Staff** from your main menu.
2. **🔗 Invite Staff**: Generates a secure Telegram Invite Link (e.g. https://t.me/Oyirubot?start=join_<hotel_id>).
   - Share this link directly with your kitchen, chef, or purchasing staff.
   - When they tap the link, they are automatically registered under your hotel without needing to choose from any hotel list!
3. **📋 Staff List**: View all registered staff members under your hotel with their status, phone number, and total orders placed.
4. **⏸️ Deactivate / ▶️ Activate Staff**: Tap any staff member to disable or enable their ordering access at any time.

---

### 2.3 Placing Orders as Hotel Admin
Hotel Admins can place orders directly for their hotel:
- **🛒 Place Order**: Browse categories (*Vegetables, Fruits, Meat, Dairy*), select items, enter quantities (e.g. 50 kg, 10 boxes), and submit.
- **📄 Upload Product List**: Send a photo of a handwritten list or upload invoices/documents (**PDF, Excel .xlsx, Word .docx, Text**).

---

### 2.4 Reviewing & Approving Orders
1. **📥 New Orders**: View pending incoming orders placed by your staff.
2. **✅ Approve Order**: Opens an interactive list of **registered delivery drivers** (🚗 Driver Name). Tap a driver to assign them immediately without typing names manually.
3. Progress order fulfillment:
   - 👨‍🍳 Start Preparing → Notifies customer preparation is underway.
   - 📦 Mark Packed → Confirms items are packed.
   - 🚚 Out for Delivery → Dispatches driver.
   - ✅ Mark Delivered → Confirms handoff.

---

### 2.5 Exporting Hotel Records (📊 Export Hotel Orders (Excel))
1. Tap **📊 Export Hotel Orders (Excel)** from your menu.
2. The bot generates and sends an official .xlsx spreadsheet containing:
   - Order numbers & Timestamps
   - Ordering Staff Name & Phone number
   - Full products list with KG/units
   - Status, Assigned Driver, and Notes.

---

## 3. Hotel Ordering Staff (Customer) Guide

Hotel Ordering Staff (Chefs, Purchasing officers, Storekeepers) place daily fresh supply orders.

### 3.1 Registration via Invite Link
1. Ask your **Hotel Admin** for your hotel's invite link.
2. Open the invite link in Telegram (e.g., https://t.me/Oyirubot?start=join_...).
3. Select your language.
4. Enter your **Full Name** and **Phone Number**.
5. You are registered directly under your hotel.

---

### 3.2 Placing Orders
- **Option A: Catalog Order (🛒 Place Order)**:
  1. Tap **🛒 Place Order** → **🧺 Category Order**.
  2. Select category & product.
  3. Enter quantity when prompted (e.g. 100kg, 12.5, 5 boxes).
  4. Add optional delivery notes.
  5. Tap **✅ Submit Order**.
- **Option B: Upload Order (📄 Upload Product List)**:
  1. Tap **🛒 Place Order** → **📄 Upload Product List**.
  2. Send a photo or document file.
  3. Review preview and tap **✅ Submit Order**.

---

### 3.3 Tracking & History (📦 My Orders)
1. Tap **📦 My Orders** to track status (Submitted → Preparing → Packed → Out for Delivery → Delivered).
2. **🔄 Reorder Last Order**: Re-order your previous grocery list in one click.
3. **📊 Export Orders (Excel)**: Download personal order history spreadsheet.
4. **Delivery Rating**: Rate your delivery experience (⭐ 1 to ⭐ 5) upon receiving goods.

---

## 4. Delivery Partner Guide (Drivers)

### 4.1 Driver Menu
- **📦 Available Deliveries**: Orders assigned to you awaiting acceptance.
- **🚚 My Deliveries**: Orders currently active.
- **📜 Delivery History**: Past delivery records.
- **📊 Export Deliveries (Excel)**: Export personal delivery logs.

### 4.2 Handling Deliveries
1. Receive assignment notification with hotel destination address and attached order photo/list.
2. Tap **✅ Accept Delivery**.
3. Tap **🚛 Out for Delivery** when leaving the warehouse.
4. Tap **✅ Complete Delivery** upon arrival and handoff at the hotel.

---

## 5. Admin & Super Admin Guide

Super Admins have complete system control across all hotels, catalogs, orders, and users.

### 5.1 Admin Menu
- **🏨 Hotels**: View all hotels, view assigned Hotel Admin and staff counts, add hotels, edit details.
- **🧺 Categories & 📦 Products**: Manage catalog items, units, and active status.
- **👥 Users**: Manage all users, change roles, assign/reassign Hotel Admins.
- **📥 New Orders**: View all system orders and assign delivery drivers.
- **📊 Statistics & 📊 Export Excel**: Real-time analytics and system-wide raw data reports.
- **📢 Broadcast**: Send instant announcements to all bot users.

---

## 6. Telegram Channel & Notification Matrix

| Event | Destination | Contents |
| :--- | :--- | :--- |
| **New Hotel Admin Registration** | Super Admin Chat | Hotel name, Admin details, Approval buttons |
| **New Staff Registration** | Super Admin & Hotel Admin Chat | Staff name, phone, Hotel name |
| **New Order Submitted** | Orders Channel, Store Managers, Inventory Group | Order card + Attached photo/document invoice |
| **Driver Assigned** | Driver Chat, Customer Chat | Destination address + Items list |
| **Order Delivered** | Orders Channel, Sales Managers | Delivery confirmation + Timestamp |
| **Customer Feedback** | Quality Control & Operations Group | Star rating (1-5) + Customer remarks |
| **Product Return** | Quality Control & Super Admin | Return reason + Uploaded photo proof |

---

## 📞 Support & Help
For technical assistance or inquiries, please contact your System Administrator.
