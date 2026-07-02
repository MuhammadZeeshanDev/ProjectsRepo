"""
Supplier panel: add, search, list and delete suppliers.
"""

import customtkinter as ctk
from tkinter import messagebox

from app.config import get_conn
from app.theme import NAVY, GRAY, TEAL
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


def db_get_suppliers(search=""):
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    if search:
        cur.execute(
            "SELECT Supplier_ID, Supplier_Name, Phone, City "
            "FROM Supplier WHERE Supplier_Name LIKE ? OR City LIKE ? "
            "ORDER BY Supplier_Name",
            (f"%{search}%", f"%{search}%"),
        )
    else:
        cur.execute(
            "SELECT Supplier_ID, Supplier_Name, Phone, City "
            "FROM Supplier ORDER BY Supplier_Name"
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def db_add_supplier(name, phone, city):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Supplier (Supplier_Name, Phone, City) VALUES (?,?,?)",
        (name, phone, city),
    )
    conn.commit()
    conn.close()


def db_delete_supplier(sid):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM Supplier WHERE Supplier_ID=?", (sid,))
    conn.commit()
    conn.close()


# ── Screen ────────────────────────────────────────────────────────


class SupplierScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=NAVY)
        self._build()
        self._load()

    def _build(self):
        section_heading(self, "🏭", "Supplier Management")

        box = form_box(self, "Add New Supplier")
        self.name_e = labeled_entry(box, "Supplier Name *", 1, 0, "e.g. Gul Ahmed Textile")
        self.phone_e = labeled_entry(box, "Phone *", 1, 1, "e.g. 0321-1234567")
        self.city_e = labeled_entry(box, "City *", 1, 2, "e.g. Karachi")

        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=6, sticky="w", padx=12, pady=(4, 14))
        primary_btn(btn_row, "➕  Add Supplier", self._add, TEAL).pack(side="left", padx=(0, 10))
        danger_btn(btn_row, "🗑  Delete Selected", self._delete).pack(side="left")

        search_bar(self, self._search, self._load)

        cols = ("ID", "Supplier Name", "Phone", "City")
        widths = (60, 260, 180, 160)
        tf, self.tree = make_treeview(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=GRAY)
        self.status.pack(anchor="w", padx=16, pady=(0, 8))

    def _load(self):
        rows = db_get_suppliers()
        fill_tree(self.tree, rows)
        self.status.configure(text=f"  Total suppliers: {len(rows)}")

    def _search(self, kw):
        rows = db_get_suppliers(kw)
        fill_tree(self.tree, rows)
        self.status.configure(text=f"  Search results: {len(rows)}")

    def _add(self):
        n = self.name_e.get().strip()
        p = self.phone_e.get().strip()
        c = self.city_e.get().strip()
        if not all([n, p, c]):
            messagebox.showwarning("Missing Fields", "Please fill Supplier Name, Phone and City.")
            return
        try:
            db_add_supplier(n, p, c)
            for e in (self.name_e, self.phone_e, self.city_e):
                e.delete(0, "end")
            self._load()
            messagebox.showinfo("Success", f"Supplier '{n}' added successfully!")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a supplier to delete.")
            return
        sid = self.tree.item(sel[0])["values"][0]
        name = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Confirm Delete", f"Delete supplier '{name}'  (ID: {sid})?"):
            try:
                db_delete_supplier(sid)
                self._load()
            except Exception as ex:
                messagebox.showerror(
                    "Cannot Delete", f"Supplier has linked orders and cannot be deleted.\n\n{ex}"
                )
