"""
Customer panel: add, search, list and delete customers.
"""

import customtkinter as ctk
from tkinter import messagebox

from app.config import get_conn
from app.theme import NAVY, GRAY
from app.widgets import (
    section_heading,
    form_box,
    labeled_entry,
    primary_btn,
    danger_btn,
    search_bar,
    make_treeview,
    fill_tree,
)

# ── Database queries ─────────────────────────────────────────────


def db_get_customers(search=""):
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    if search:
        cur.execute(
            "SELECT Customer_ID, Customer_Name, Phone, City "
            "FROM Customer WHERE Customer_Name LIKE ? OR City LIKE ? "
            "ORDER BY Customer_Name",
            (f"%{search}%", f"%{search}%"),
        )
    else:
        cur.execute(
            "SELECT Customer_ID, Customer_Name, Phone, City "
            "FROM Customer ORDER BY Customer_Name"
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def db_add_customer(name, phone, city):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Customer (Customer_Name, Phone, City) VALUES (?,?,?)",
        (name, phone, city),
    )
    conn.commit()
    conn.close()


def db_delete_customer(cid):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM Customer WHERE Customer_ID=?", (cid,))
    conn.commit()
    conn.close()


# ── Screen ────────────────────────────────────────────────────────


class CustomerScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=NAVY)
        self._build()
        self._load()

    def _build(self):
        section_heading(self, "👥", "Customer Management")

        box = form_box(self, "Add New Customer")
        self.name_e = labeled_entry(box, "Full Name *", 1, 0, "e.g. Ahmed Ali")
        self.phone_e = labeled_entry(box, "Phone *", 1, 1, "e.g. 0312-1234567")
        self.city_e = labeled_entry(box, "City *", 1, 2, "e.g. Karachi")

        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=6, sticky="w", padx=12, pady=(4, 14))
        primary_btn(btn_row, "➕  Add Customer", self._add).pack(side="left", padx=(0, 10))
        danger_btn(btn_row, "🗑  Delete Selected", self._delete).pack(side="left")

        search_bar(self, self._search, self._load)

        cols = ("ID", "Customer Name", "Phone", "City")
        widths = (60, 260, 180, 160)
        tf, self.tree = make_treeview(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=GRAY)
        self.status.pack(anchor="w", padx=16, pady=(0, 8))

    def _load(self):
        rows = db_get_customers()
        fill_tree(self.tree, rows)
        self.status.configure(text=f"  Total customers: {len(rows)}")

    def _search(self, kw):
        rows = db_get_customers(kw)
        fill_tree(self.tree, rows)
        self.status.configure(text=f"  Search results: {len(rows)}")

    def _add(self):
        n = self.name_e.get().strip()
        p = self.phone_e.get().strip()
        c = self.city_e.get().strip()
        if not all([n, p, c]):
            messagebox.showwarning(
                "Missing Fields", "Please fill Name, Phone and City before adding."
            )
            return
        try:
            db_add_customer(n, p, c)
            for e in (self.name_e, self.phone_e, self.city_e):
                e.delete(0, "end")
            self._load()
            messagebox.showinfo("Success", f"Customer '{n}' added successfully!")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                "No Selection", "Please select a customer from the table to delete."
            )
            return
        cid = self.tree.item(sel[0])["values"][0]
        name = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete customer:\n\n"
            f"  {name}  (ID: {cid})\n\n"
            f"Note: Cannot delete if customer has existing orders.",
        ):
            try:
                db_delete_customer(cid)
                self._load()
            except Exception as ex:
                messagebox.showerror(
                    "Cannot Delete",
                    "This customer cannot be deleted because they have existing "
                    f"orders.\n\nDelete the orders first, then delete the customer.\n\n{ex}",
                )
