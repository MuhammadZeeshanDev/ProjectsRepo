"""
Order panel: place new orders against a customer, shop, fabric and
supplier, track payment status, and browse order history.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date

from app.config import get_conn
from app.theme import NAVY, GRAY, GOLD, SUCCESS
from app.widgets import (
    section_heading,
    form_box,
    labeled_entry,
    labeled_dropdown,
    primary_btn,
    danger_btn,
    info_btn,
    search_bar,
    make_treeview,
    fill_tree,
)
from app.customer_panel import db_get_customers
from app.supplier_panel import db_get_suppliers
from app.fabric_panel import db_get_fabrics
from app.shop_panel import db_get_shops_dropdown

# ── Database queries ─────────────────────────────────────────────


def db_get_orders(search=""):
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    sql = """
        SELECT
            o.Order_ID,
            CONVERT(VARCHAR, o.Order_Date, 23) AS Order_Date,
            c.Customer_Name,
            s.Shop_Name,
            f.Fabric_Name,
            sup.Supplier_Name,
            o.Quantity_Meters,
            o.Price_Per_Meter,
            o.Discount_Percent,
            o.Total_Amount,
            o.Payment_Method,
            o.Payment_Status
        FROM Orders o
        INNER JOIN Customer  c   ON o.Customer_ID  = c.Customer_ID
        INNER JOIN Shop      s   ON o.Shop_ID      = s.Shop_ID
        INNER JOIN Fabric    f   ON o.Fabric_ID    = f.Fabric_ID
        INNER JOIN Supplier  sup ON o.Supplier_ID  = sup.Supplier_ID
    """
    if search:
        sql += (
            " WHERE c.Customer_Name LIKE ? OR f.Fabric_Name LIKE ? "
            "OR o.Payment_Status LIKE ?"
        )
        sql += " ORDER BY o.Order_Date DESC"
        cur.execute(sql, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        sql += " ORDER BY o.Order_Date DESC"
        cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows


def db_add_order(order_date, cid, shopid, fabid, supid, qty, price, disc, total, method, status):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Orders (
            Order_Date, Customer_ID, Shop_ID, Fabric_ID, Supplier_ID,
            Quantity_Meters, Price_Per_Meter, Discount_Percent,
            Total_Amount, Payment_Method, Payment_Status
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (order_date, cid, shopid, fabid, supid, qty, price, disc, total, method, status),
    )
    conn.commit()
    conn.close()


def db_delete_order(oid):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM Orders WHERE Order_ID=?", (oid,))
    conn.commit()
    conn.close()


def db_update_payment(oid, status):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("UPDATE Orders SET Payment_Status=? WHERE Order_ID=?", (status, oid))
    conn.commit()
    conn.close()


# ── Screen ────────────────────────────────────────────────────────


class OrderScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=NAVY)
        self._cust_map = {}
        self._sup_map = {}
        self._fab_map = {}
        self._shop_map = {}
        self._build()
        self._load()

    def _build(self):
        section_heading(self, "📦", "Order Management")

        box = form_box(self, "Place New Order")

        custs = db_get_customers()
        sups = db_get_suppliers()
        fabs = db_get_fabrics()
        shops = db_get_shops_dropdown()

        self._cust_map = {f"{r[1]}": r[0] for r in custs}
        self._sup_map = {f"{r[1]}": r[0] for r in sups}
        self._fab_map = {f"{r[1]}": (r[0], float(r[3])) for r in fabs}
        self._shop_map = {f"{r[1]}": r[0] for r in shops}

        self.cust_dd = labeled_dropdown(box, "Customer *", 1, 0, list(self._cust_map.keys()), width=210)
        self.sup_dd = labeled_dropdown(box, "Supplier *", 1, 1, list(self._sup_map.keys()), width=210)
        self.fab_dd = labeled_dropdown(box, "Fabric *", 1, 2, list(self._fab_map.keys()), width=210)
        self.shop_dd = labeled_dropdown(box, "Shop *", 1, 3, list(self._shop_map.keys()), width=210)

        self.qty_e = labeled_entry(box, "Qty (meters)*", 2, 0, "e.g. 20", width=130)
        self.disc_e = labeled_entry(box, "Discount % ", 2, 1, "0 – 100", width=130)
        self.meth_dd = labeled_dropdown(
            box, "Payment Method *", 2, 2, ["Cash", "Bank Transfer", "Cheque", "Online Payment"], width=180
        )
        self.stat_dd = labeled_dropdown(box, "Payment Status *", 2, 3, ["Paid", "Unpaid", "Partial"], width=180)

        total_row = ctk.CTkFrame(box, fg_color="transparent")
        total_row.grid(row=3, column=0, columnspan=8, sticky="w", padx=12, pady=(4, 4))
        self.total_lbl = ctk.CTkLabel(
            total_row, text="  Total Amount:  PKR 0.00", font=("Segoe UI", 14, "bold"), text_color=GOLD
        )
        self.total_lbl.pack(side="left")

        self.qty_e.bind("<KeyRelease>", lambda e: self._calc())
        self.disc_e.bind("<KeyRelease>", lambda e: self._calc())
        self.fab_dd.configure(command=lambda v: self._calc())

        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.grid(row=4, column=0, columnspan=8, sticky="w", padx=12, pady=(4, 14))
        primary_btn(btn_row, "✅  Place Order", self._add_order, SUCCESS, 180).pack(side="left", padx=(0, 10))
        danger_btn(btn_row, "🗑  Delete Selected", self._delete_order, 180).pack(side="left", padx=(0, 10))
        info_btn(btn_row, "💳  Mark as Paid", self._mark_paid, 160).pack(side="left")

        search_bar(self, self._search, self._load)

        cols = ("ID", "Date", "Customer", "Shop", "Fabric", "Supplier", "Qty(m)", "Price/m", "Disc%", "Total PKR", "Method", "Status")
        widths = (50, 90, 150, 140, 100, 150, 60, 70, 50, 100, 120, 80)
        tf, self.tree = make_treeview(self, cols, widths, height=10)
        tf.pack(fill="both", expand=True, padx=16, pady=(4, 6))

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=GRAY)
        self.status.pack(anchor="w", padx=16, pady=(0, 8))

    def _calc(self):
        """Recomputes the order total whenever qty, discount or fabric changes."""
        try:
            fab_key = self.fab_dd.get()
            price = self._fab_map.get(fab_key, (0, 0.0))[1]
            qty = float(self.qty_e.get() or 0)
            disc = float(self.disc_e.get() or 0)
            total = price * qty * (1 - disc / 100)
            self.total_lbl.configure(text=f"  Total Amount:  PKR {total:,.2f}")
        except (ValueError, TypeError):
            self.total_lbl.configure(text="  Total Amount:  PKR 0.00")

    def _load(self):
        rows = db_get_orders()
        formatted = [
            (r[0], r[1], r[2], r[3], r[4], r[5], r[6], f"{float(r[7]):,.2f}", f"{r[8]}%", f"{float(r[9]):,.2f}", r[10], r[11])
            for r in rows
        ]
        fill_tree(self.tree, formatted)
        self.status.configure(text=f"  Total orders: {len(rows)}")

    def _search(self, kw):
        rows = db_get_orders(kw)
        formatted = [
            (r[0], r[1], r[2], r[3], r[4], r[5], r[6], f"{float(r[7]):,.2f}", f"{r[8]}%", f"{float(r[9]):,.2f}", r[10], r[11])
            for r in rows
        ]
        fill_tree(self.tree, formatted)
        self.status.configure(text=f"  Search results: {len(rows)}")

    def _add_order(self):
        try:
            fab_key = self.fab_dd.get()
            if fab_key not in self._fab_map:
                messagebox.showwarning("Select Fabric", "Please select a valid fabric.")
                return
            fab_id = self._fab_map[fab_key][0]
            price = self._fab_map[fab_key][1]
            qty = int(self.qty_e.get().strip())
            disc = int(self.disc_e.get().strip() or 0)
            total = round(price * qty * (1 - disc / 100), 2)
            cid = self._cust_map.get(self.cust_dd.get())
            sid = self._sup_map.get(self.sup_dd.get())
            shopid = self._shop_map.get(self.shop_dd.get())
            method = self.meth_dd.get()
            status = self.stat_dd.get()
            odate = str(date.today())

            if not all([cid, sid, shopid]):
                messagebox.showwarning("Missing", "Please select Customer, Supplier and Shop.")
                return
            if qty <= 0:
                messagebox.showwarning("Invalid Qty", "Quantity must be greater than 0.")
                return

            db_add_order(odate, cid, shopid, fab_id, sid, qty, price, disc, total, method, status)
            self.qty_e.delete(0, "end")
            self.disc_e.delete(0, "end")
            self.total_lbl.configure(text="  Total Amount:  PKR 0.00")
            self._load()
            messagebox.showinfo(
                "Order Placed",
                f"Order placed successfully!\n\nFabric : {fab_key}\nQty    : {qty} meters\n"
                f"Total  : PKR {total:,.2f}\nStatus : {status}",
            )
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Quantity and Discount must be numbers.\nExample: Qty = 20, Discount = 10"
            )
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _delete_order(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select an order to delete.")
            return
        oid = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", f"Delete Order ID {oid}?\nThis cannot be undone."):
            try:
                db_delete_order(oid)
                self._load()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

    def _mark_paid(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select an order to mark as Paid.")
            return
        oid = self.tree.item(sel[0])["values"][0]
        status = self.tree.item(sel[0])["values"][11]
        if status == "Paid":
            messagebox.showinfo("Already Paid", f"Order {oid} is already marked as Paid.")
            return
        if messagebox.askyesno("Mark as Paid", f"Mark Order {oid} as Paid?"):
            try:
                db_update_payment(oid, "Paid")
                self._load()
                messagebox.showinfo("Updated", f"Order {oid} marked as Paid.")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
