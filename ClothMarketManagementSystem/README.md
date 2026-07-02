# Cloth Market Management System

A desktop application for managing the day-to-day operations of a wholesale cloth market business. It replaces manual, Excel-based record keeping with a proper relational database connected to a clean, easy-to-use interface.

---

## Who Is This For?

- **Shop owners** in wholesale cloth markets (Jodia Bazaar, Bohri Bazaar, Liberty Market, etc.)
- **Market managers** who deal with multiple suppliers, fabric types, and regular customers
- **Staff members** responsible for recording orders and tracking payments

If your business currently uses Excel to track customers, orders, suppliers, and payments, this system is built for you.

---

## What Does It Do?

| Module      | What You Can Do |
|-------------|-----------------|
| Dashboard   | View KPI cards (orders, customers, revenue, unpaid orders, suppliers), recent orders, and two charts built from live order data |
| Customers   | Add, search, and delete customer records |
| Suppliers   | Add, search, and delete supplier records |
| Fabrics     | Add, search, and delete fabric types with price per meter |
| Shops       | Add, search, and delete shops with owner name, phone, location and city |
| Orders      | Place orders using dropdowns, auto-calculate total, track payment status |

Every change made in the app is saved directly to the SQL Server database in real time — nothing is cached locally.

### Dashboard Charts

- **Top Fabrics by Revenue** — horizontal bar chart comparing revenue earned per fabric, so the highest-selling fabric is easy to spot at a glance.
- **Orders by Payment Status** — donut chart showing the proportion of Paid, Unpaid and Partial orders, useful for tracking outstanding payments.

Both charts are rendered with matplotlib and refresh with whatever data is currently in the database.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language  | Python 3.10+ |
| GUI       | CustomTkinter |
| Charts    | matplotlib |
| Database  | Microsoft SQL Server 2022 |
| Connector | pyodbc |

---

## Project Structure

```
ClothMarketManagementSystem/
│
├── main.py                    ← Run this to start the app
├── requirements.txt
├── LICENSE
├── README.md
│
├── app/
│   ├── config.py               ← Database connection settings
│   ├── theme.py                ← Shared color palette
│   ├── widgets.py               ← Reusable UI components (tables, forms, buttons)
│   ├── login_panel.py           ← Login screen
│   ├── main_window.py           ← Sidebar navigation + screen switching
│   ├── dashboard_panel.py       ← Dashboard: KPI cards + charts
│   ├── customer_panel.py        ← Customer panel (UI + queries)
│   ├── supplier_panel.py        ← Supplier panel (UI + queries)
│   ├── fabric_panel.py          ← Fabric panel (UI + queries)
│   ├── shop_panel.py            ← Shop panel (UI + queries)
│   └── order_panel.py           ← Order panel (UI + queries)
│
└── database/
    └── cloth_market.sql        ← Run this in SSMS first
```

Each panel is self-contained: its screen class and its own database queries live in the same file, so you can open `app/shop_panel.py`, for example, and see everything the Shops screen does in one place.

---

## Setup Instructions

### Step 1 — Run the Database Script

1. Open **SQL Server Management Studio (SSMS)**
2. Open `database/cloth_market.sql`
3. Click **Execute** (or press F5)
4. This creates `ClothMarketDB` with all tables and sample data. The script drops and recreates tables if they already exist, so it's safe to re-run.

### Step 2 — Install Python Libraries

```
pip install -r requirements.txt
```

### Step 3 — Update the Server Name

Open `app/config.py` and find:

```python
SERVER   = "localhost"
DATABASE = "ClothMarketDB"
```

Change `localhost` to your SQL Server instance name if needed. To find it, open SSMS — the server name shown in the login box is what you need.

Common examples:
- `localhost`
- `DESKTOP-ABC123\SQLEXPRESS`
- `.\SQLEXPRESS`

### Step 4 — Run the App

```
python main.py
```

**Login credentials:**
- Username: `admin`
- Password: `admin123`

---

## How to Use

### Dashboard
Opens automatically after login. Shows live stats — total orders, customers, revenue, unpaid orders, and suppliers — plus the 5 most recent orders and the two revenue/payment charts described above.

### Adding a Customer
1. Click **Customers** in the sidebar
2. Fill in Name, Phone, and City in the form at the top
3. Click **Add Customer**
4. The table updates immediately

### Adding a Shop
1. Click **Shops** in the sidebar
2. Fill in Shop Name, Owner Name, Phone, Location and City
3. Click **Add Shop** — the new shop appears in the table right away and becomes available in the Shop dropdown on the Orders screen

### Placing an Order
1. Click **Orders** in the sidebar
2. Select Customer, Supplier, Fabric, and Shop from the dropdowns
3. Enter Quantity and Discount % (leave discount blank for 0%)
4. The Total Amount calculates automatically
5. Select Payment Method and Payment Status
6. Click **Place Order**

### Marking an Order as Paid
1. Go to **Orders**
2. Click on any unpaid order in the table
3. Click **Mark as Paid**

### Searching Records
Every screen has a search bar. Type a name or city and press Enter or click Search. Click Clear to reset.

### Deleting Records
Select any row in the table and click Delete. You cannot delete a customer, supplier, shop, or fabric that has existing orders linked to it — delete the orders first.

---

## Database Tables

| Table    | Columns |
|----------|---------|
| Customer | Customer_ID, Customer_Name, Phone, City |
| Supplier | Supplier_ID, Supplier_Name, Phone, City |
| Fabric   | Fabric_ID, Fabric_Name, Category, Price_Per_Meter |
| Shop     | Shop_ID, Shop_Name, Owner_Name, Phone, Location, City |
| Orders   | Order_ID, Order_Date, Customer_ID, Shop_ID, Fabric_ID, Supplier_ID, Quantity_Meters, Price_Per_Meter, Discount_Percent, Total_Amount, Payment_Method, Payment_Status |

---

## Common Issues

**App says cannot connect to database**
- Make sure SQL Server 2022 is running (check in Windows Services)
- Make sure you ran `cloth_market.sql` in SSMS
- Check the `SERVER` name in `app/config.py`

**A panel looks empty**
- This means the query ran but returned zero rows — either the table is genuinely empty (use the form on that screen to add a record) or the connection failed silently. Check the status bar at the bottom of the screen for a message.

**pyodbc not found**
- Run: `pip install pyodbc`

**ODBC Driver error**
- Download and install: Microsoft ODBC Driver 17 for SQL Server

**Charts not showing / matplotlib import error**
- Run: `pip install matplotlib`

**Table not found error**
- You may not have run the SQL script yet — open SSMS, open `cloth_market.sql`, and run it

---

## Course Information

- **Course:** CT-261 Database Management Systems
- **University:** NED University of Engineering and Technology
- **Instructor:** Abdul Hafeez Babar
