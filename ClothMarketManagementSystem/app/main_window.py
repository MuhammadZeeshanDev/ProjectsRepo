"""
Main window shown after login: sidebar navigation on the left, the
active panel on the right.
"""

import traceback

import customtkinter as ctk
from tkinter import messagebox

from app.theme import NAVY, SIDEBAR, ACCENT, LIGHT, WHITE, GRAY, CARD, DANGER
from app.dashboard_panel import DashboardScreen
from app.customer_panel import CustomerScreen
from app.supplier_panel import SupplierScreen
from app.fabric_panel import FabricScreen
from app.shop_panel import ShopScreen
from app.order_panel import OrderScreen

NAV_ITEMS = [
    ("📊", "Dashboard", "dashboard"),
    ("👥", "Customers", "customers"),
    ("🏭", "Suppliers", "suppliers"),
    ("🧶", "Fabrics", "fabrics"),
    ("🏪", "Shops", "shops"),
    ("📦", "Orders", "orders"),
]

SCREENS = {
    "dashboard": DashboardScreen,
    "customers": CustomerScreen,
    "suppliers": SupplierScreen,
    "fabrics": FabricScreen,
    "shops": ShopScreen,
    "orders": OrderScreen,
}


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cloth Market Management System")
        self.geometry("1280x740")
        self.minsize(1100, 660)
        self.configure(fg_color=NAVY)
        self._current = None
        self._build()
        self._show("dashboard")

    def _build(self):
        sb = ctk.CTkFrame(self, fg_color=SIDEBAR, width=220, corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        logo = ctk.CTkFrame(sb, fg_color=ACCENT, corner_radius=0, height=90)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="🧵", font=("Segoe UI", 34)).pack(pady=(14, 2))
        ctk.CTkLabel(logo, text="Cloth Market", font=("Segoe UI", 14, "bold"), text_color=WHITE).pack()

        ctk.CTkFrame(sb, height=1, fg_color="#1A4A6A").pack(fill="x", pady=(10, 6))
        ctk.CTkLabel(sb, text="  MAIN MENU", font=("Segoe UI", 10), text_color=GRAY).pack(
            anchor="w", padx=14, pady=(0, 4)
        )

        self._nav_btns = {}
        for icon, label, key in NAV_ITEMS:
            btn = ctk.CTkButton(
                sb,
                text=f"  {icon}  {label}",
                anchor="w",
                height=48,
                font=("Segoe UI", 13),
                fg_color="transparent",
                text_color=LIGHT,
                hover_color="#1A3A52",
                corner_radius=0,
                command=lambda k=key: self._show(k),
            )
            btn.pack(fill="x", pady=1)
            self._nav_btns[key] = btn

        ctk.CTkFrame(sb, height=1, fg_color="#1A4A6A").pack(fill="x", pady=(12, 0), side="bottom")
        ctk.CTkButton(
            sb,
            text="  🚪  Logout",
            anchor="w",
            height=48,
            font=("Segoe UI", 13),
            fg_color="transparent",
            text_color="#E74C3C",
            hover_color="#3D0A0A",
            corner_radius=0,
            command=self._logout,
        ).pack(fill="x", side="bottom")

        ctk.CTkLabel(
            sb, text="  CT-261 DBMS  |  NED University", font=("Segoe UI", 9), text_color="#2A4A5A"
        ).pack(side="bottom", anchor="w", padx=10, pady=6)

        self.content = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

    def _show(self, key):
        for k, btn in self._nav_btns.items():
            btn.configure(
                fg_color=ACCENT if k == key else "transparent",
                font=("Segoe UI", 13, "bold" if k == key else "normal"),
            )

        if self._current:
            self._current.destroy()
            self._current = None

        try:
            self._current = SCREENS[key](self.content)
        except Exception as ex:
            # A panel should never fail silently and leave a blank screen -
            # show the real error here instead, plus print the full
            # traceback to the console for debugging.
            traceback.print_exc()
            self._current = self._error_panel(key, ex)

        self._current.pack(fill="both", expand=True)

    def _error_panel(self, key, ex):
        panel = ctk.CTkFrame(self.content, fg_color=NAVY)
        box = ctk.CTkFrame(panel, fg_color=CARD, corner_radius=14)
        box.pack(expand=True, padx=60, pady=60)
        ctk.CTkLabel(box, text="⚠️", font=("Segoe UI", 40)).pack(pady=(24, 6))
        ctk.CTkLabel(
            box,
            text=f"Could not load the '{key.title()}' screen",
            font=("Segoe UI", 16, "bold"),
            text_color=WHITE,
        ).pack(pady=(0, 6), padx=30)
        ctk.CTkLabel(
            box,
            text=str(ex),
            font=("Segoe UI", 12),
            text_color=DANGER,
            wraplength=420,
            justify="left",
        ).pack(pady=(0, 16), padx=30)
        ctk.CTkButton(
            box,
            text="🔄  Try Again",
            fg_color=ACCENT,
            hover_color="#155882",
            command=lambda: self._show(key),
        ).pack(pady=(0, 24))
        return panel

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            # Imported here to avoid a circular import with login_panel.
            from app.login_panel import LoginApp

            LoginApp().mainloop()