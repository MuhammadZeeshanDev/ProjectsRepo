"""
Fabric panel: add, search, list and delete fabric types with their
price per meter.
"""

import customtkinter as ctk
from tkinter import messagebox

from app.config import get_conn
from app.theme import NAVY, GRAY, GOLD
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


def db_get_fabrics(search=""):
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    if search:
        cur.execute(
            "SELECT Fabric_ID, Fabric_Name, Category, Price_Per_Meter "
            "FROM Fabric WHERE Fabric_Name LIKE ? OR Category LIKE ? "
            "ORDER BY Fabric_Name",
            (f"%{search}%", f"%{search}%"),
        )
    else:
        cur.execute(
            "SELECT Fabric_ID, Fabric_Name, Category, Price_Per_Meter "
            "FROM Fabric ORDER BY Fabric_Name"
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def db_add_fabric(name, category, price):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Fabric (Fabric_Name, Category, Price_Per_Meter) VALUES (?,?,?)",
        (name, category, price),
    )
    conn.commit()
    conn.close()


def db_delete_fabric(fid):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM Fabric WHERE Fabric_ID=?", (fid,))
    conn.commit()
    conn.close()


# ── Screen ────────────────────────────────────────────────────────


class FabricScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=NAVY)
        self._build()
        self._load()

    def _build(self):
        section_heading(self, "🧶", "Fabric Management")

        box = form_box(self, "Add New Fabric")
        self.name_e = labeled_entry(box, "Fabric Name *", 1, 0, "e.g. Lawn")
        self.cat_e = labeled_entry(box, "Category *", 1, 1, "e.g. Summer Fabric")
        self.price_e = labeled_entry(box, "Price/Meter *", 1, 2, "e.g. 350")

        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=6, sticky="w", padx=12, pady=(4, 14))
        primary_btn(btn_row, "➕  Add Fabric", self._add, GOLD).pack(side="left", padx=(0, 10))
        danger_btn(btn_row, "🗑  Delete Selected", self._delete).pack(side="left")

        search_bar(self, self._search, self._load)

        cols = ("ID", "Fabric Name", "Category", "Price / Meter (PKR)")
        widths = (60, 220, 200, 200)
        tf, self.tree = make_treeview(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=GRAY)
        self.status.pack(anchor="w", padx=16, pady=(0, 8))

    def _load(self):
        rows = db_get_fabrics()
        fill_tree(self.tree, [(r[0], r[1], r[2], f"{float(r[3]):,.2f}") for r in rows])
        self.status.configure(text=f"  Total fabric types: {len(rows)}")

    def _search(self, kw):
        rows = db_get_fabrics(kw)
        fill_tree(self.tree, [(r[0], r[1], r[2], f"{float(r[3]):,.2f}") for r in rows])
        self.status.configure(text=f"  Search results: {len(rows)}")

    def _add(self):
        n = self.name_e.get().strip()
        c = self.cat_e.get().strip()
        p = self.price_e.get().strip()
        if not all([n, c, p]):
            messagebox.showwarning("Missing Fields", "Please fill Fabric Name, Category and Price.")
            return
        try:
            price = float(p)
            if price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Price", "Price must be a positive number (e.g. 350 or 1200.50)."
            )
            return
        try:
            db_add_fabric(n, c, price)
            for e in (self.name_e, self.cat_e, self.price_e):
                e.delete(0, "end")
            self._load()
            messagebox.showinfo("Success", f"Fabric '{n}' added successfully!")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a fabric to delete.")
            return
        fid = self.tree.item(sel[0])["values"][0]
        name = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Confirm Delete", f"Delete fabric '{name}'?"):
            try:
                db_delete_fabric(fid)
                self._load()
            except Exception as ex:
                messagebox.showerror(
                    "Cannot Delete", f"Fabric has linked orders and cannot be deleted.\n\n{ex}"
                )
