# 📖 Oyirubot — Comprehensive User Manual & Operations Guide

Welcome to **Oyirubot**, the automated order management and delivery dispatch system for hotels, restaurants, and fresh food supply chains.

---

## 📑 Table of Contents
1. [🌐 General Getting Started & Language Selection](#1-getting-started--language-selection)
2. [👤 Customer Guide (Hotel Ordering Staff)](#2-customer-guide)
3. [🏨 Store Manager Guide (Hotel Dispatchers & Kitchen)](#3-store-manager-guide)
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

## 2. Customer Guide

### 2.1 Registration
1. Send /start to the bot.
2. Select your preferred language (**English / አማርኛ / Afaan Oromoo**).
3. Select your assigned **Hotel / Restaurant branch** from the list.
4. Tap **📱 Share Contact** to verify your phone number.
5. Enter your **Full Name**.
6. Once registered, your account is activated (or queued for admin confirmation).

---

### 2.2 Placing an Order

Customers can place orders using either **Catalog Browsing** or **Direct File/Photo Upload**:

#### Option A: Catalog Browsing (🛒 Place Order)
1. Tap **🛒 Place Order** from the main menu.
2. Choose **📂 Browse Categories**.
3. Select the category (e.g., *Vegetables*, *Fruits*, *Meat*, *Dairy*).
4. Tap the products you want to order.
5. Enter the quantity when prompted. Examples are shown for clarity:
   - For items in KG: 50, 12.5, 500kg, or 100 kilo
   - For items in PCS / Box: 10, 5 boxes, 20 pcs
6. Add optional order notes (e.g., *"Deliver before 9:00 AM"* or *"Ripe tomatoes preferred"*).
7. Review your order summary and tap **✅ Submit Order**.

#### Option B: Photo / File Upload (📁 Upload Order)
1. Tap **🛒 Place Order** → **📁 Upload Order (Photo/Document)**.
2. Send a photo of your handwritten order list, invoice, or upload a document (**PDF, Excel .xlsx, Word .docx, or Text file**).
3. Enter an optional order note or tap **⏭️ Skip Note**.
4. Review the preview and tap **✅ Submit Order**.

---

### 2.3 Tracking Your Orders (📦 My Orders)
1. Tap **📦 My Orders** to view your active and past orders.
2. Tap on any order (e.g. 🆔 OYR-20260824-0001) to see:
   - Live Order Status:
     - ⏳ Submitted → Order received
     - 👨‍🍳 Preparing → Kitchen/Store is packing your items
     - 📦 Packed → Ready for driver pickup
     - 🚗 Out for Delivery → Driver is on the way (driver name & phone number provided)
     - ✅ Delivered → Successfully received
   - Full product list and attached invoices/photos.
3. **Repeat Order**: Tap **🔄 Repeat Order** on past orders to re-order the same items in one tap.

---

### 2.4 Rating & Delivery Feedback
When an order is delivered:
1. You will receive a delivery confirmation message.
2. Tap a rating from **⭐ 1** to **⭐ 5**.
3. Provide optional feedback to ensure top-quality service.

---

### 2.5 Exporting Orders to Excel (📊 Export Orders)
1. Tap **📊 Export Orders (Excel)** from your menu.
2. The bot generates and sends an official formatted .xlsx spreadsheet of all your order history.

---

## 3. Store Manager Guide

Store Managers oversee hotel order fulfillment, preparation, and driver dispatching.

### 3.1 Main Menu Options
- **📥 New Orders**: View incoming pending orders.
- **📦 Active Orders**: View orders currently in progress.
- **📜 Order History**: Completed & delivered orders.

---

### 3.2 Reviewing & Approving Orders
1. Tap **📥 New Orders**.
2. The bot presents the order card, including:
   - Order Number & Customer Name
   - Product list with quantities OR the attached photo/document invoice.
3. Tap **✅ Approve Order**.
4. The bot shows an interactive list of **registered delivery drivers** (🚗 Driver Name).
5. Tap the driver you wish to assign:
   - The driver is instantly notified with the order details and attached media.
   - The customer is notified that the order has been approved.

---

### 3.3 Progressing Order Stages
On the active order card, advance the order as it is prepared:
- 👨‍🍳 Start Preparing → Notifies customer that preparation has started.
- 📦 Mark Packed → Confirms items are packed and ready for pickup.
- 🚛 Send Out for Delivery → Dispatches driver to destination.
- ✅ Mark Delivered → Confirms final handoff.

---

## 4. Delivery Partner Guide

Delivery Partners (Drivers) receive assignments, navigate deliveries, and update handoffs.

### 4.1 Driver Menu
- **📦 Available Deliveries**: Orders assigned to you awaiting acceptance.
- **🚚 My Deliveries**: Orders currently active and out for delivery.
- **📜 Delivery History**: Completed delivery log.
- **📊 Export Deliveries (Excel)**: Export personal delivery logs.

---

### 4.2 Handling a Delivery
1. **Assignment Notification**: When an order is assigned to you, you receive a direct notification with:
   - Order Number & Hotel Destination Address
   - Attached photo, invoice, or item breakdown
2. Tap **✅ Accept Delivery** to accept the assignment.
3. Once the package is picked up, tap **🚛 Start Delivery / Out for Delivery**.
4. When arrived at the hotel and handed over to the receiving staff, tap **🏁 Mark Delivered**.
5. The customer and management are instantly notified of the completed delivery.

---

## 5. Admin & Super Admin Guide

Admins have complete control over catalog, hotels, users, orders, and system analytics.

### 5.1 Admin Menu
- **🏨 Hotels**: Manage registered hotel branches.
- **🧺 Categories**: Manage product categories.
- **📦 Products**: Add, edit, activate/deactivate, or delete catalog items.
- **👥 Users**: Manage user accounts and switch user roles.
- **📥 New Orders**: View all pending orders and assign drivers.
- **📊 Statistics**: View real-time revenue, order counts, and delivery metrics.
- **📊 Export Excel**: Download system-wide raw data reports.
- **📢 Broadcast**: Send announcements to all bot users.

---

### 5.2 Approving New Users
When a new staff member registers:
1. Super Admins receive an approval prompt:
   - Name, Phone, Role, and Hotel.
2. Tap **✅ Approve** to activate the user or **❌ Reject** to deny access.

---

### 5.3 Managing Products & Categories
1. Tap **🧺 Categories** → **➕ Add Category** to create a category.
2. Tap **📦 Products** → select a category → **➕ Add Product**:
   - Enter product name (e.g. *Red Onion*).
   - Enter measurement unit (e.g. *KG*, *Box*, *Liter*, *Pcs*).
3. To edit or deactivate an item:
   - Tap **📦 Products** → Select Product → Tap **✏️ Edit Name**, **✏️ Edit Unit**, or **🔴 Deactivate**.

---

### 5.4 Assigning Drivers as Admin
1. Tap **📥 New Orders**.
2. Tap **🚚 Assign Driver** on any pending order.
3. Select an active driver from the interactive driver list.

---

### 5.5 Sending Announcements (📢 Broadcast)
1. Tap **📢 Broadcast**.
2. Type your announcement message.
3. The message is broadcasted to all active bot users.

---

## 6. Channel & Group Notifications

Oyirubot automatically synchronizes events with designated Telegram channels & groups with attached media:

| Event | Notification Destination | Contents |
| :--- | :--- | :--- |
| **New Order Submitted** | Orders Channel, Store Managers, Inventory Group | Order details + Attached invoice/photo |
| **Driver Assigned** | Driver Chat, Customer Chat | Delivery address + Items list |
| **Order Delivered** | Orders Channel, Sales Managers | Delivery confirmation + Timestamp |
| **Customer Feedback** | Quality Control & Operations Group | Star rating (1-5) + Customer remarks |
| **Product Return** | Quality Control & Admin | Return reason + Uploaded photo proof |

---

## 📞 Support & Help
For technical assistance or inquiries, please contact your System Administrator.
