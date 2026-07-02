# =============================================================
#  CLOTH MARKET MANAGEMENT SYSTEM
#  Developer  : Muhammad (NED University - CT-261 DBMS Project)
#  Language   : Python 3.10+
#  GUI        : CustomTkinter
#  Database   : Microsoft SQL Server 2022
#  Connector  : pyodbc
# =============================================================
#
#  WHAT THIS APP DOES
#  Manages a wholesale cloth market: customers, suppliers,
#  fabrics, shops and orders, all backed by SQL Server so every
#  change is saved in real time.
#
#  HOW TO RUN
#  1. Run database/cloth_market.sql in SSMS first
#  2. pip install -r requirements.txt
#  3. Update SERVER in app/config.py to match your SQL Server name
#  4. python main.py
#  5. Login: admin / admin123
#
#  PROJECT LAYOUT
#  app/config.py          - database connection
#  app/theme.py            - shared color palette
#  app/widgets.py          - reusable UI components
#  app/login_panel.py      - login screen
#  app/main_window.py      - sidebar + screen switching
#  app/dashboard_panel.py  - dashboard, KPIs and charts
#  app/customer_panel.py   - customer CRUD
#  app/supplier_panel.py   - supplier CRUD
#  app/fabric_panel.py     - fabric CRUD
#  app/shop_panel.py       - shop CRUD
#  app/order_panel.py      - order placement and tracking
# =============================================================

import customtkinter as ctk

from app.login_panel import LoginApp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if __name__ == "__main__":
    LoginApp().mainloop()
