"""
Shop panel: add, search, list and delete shops.

Each shop belongs to a market (e.g. Jodia Bazaar, Liberty Market) and
is the point of sale referenced by every order in the Orders panel,
so this table needs to be filled in before any order can be placed.
"""

import customtkinter as ctk
from tkinter import messagebox

from app.config import get_conn
from app.theme import NAVY, GRAY, PURPLE
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


def db_get_shops(search=""):
    """Returns every shop, or shops matching the search text."""
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    if search:
        cur.execute(
            "SELECT Shop_ID, Shop_Name, Owner_Name, Phone, Location, City "
            "FROM Shop WHERE Shop_Name LIKE ? OR City LIKE ? OR Owner_Name LIKE ? "
            "ORDER BY Shop_Name",
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        )
    else:
        cur.execute(
            "SELECT Shop_ID, Shop_Name, Owner_Name, Phone, Location, City "
            "FROM Shop ORDER BY Shop_Name"
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def db_add_shop(name, owner, phone, location, city):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Shop (Shop_Name, Owner_Name, Phone, Location, City) "
        "VALUES (?,?,?,?,?)",
        (name, owner, phone, location, city),
    )
    conn.commit()
    conn.close()


def db_delete_shop(sid):
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM Shop WHERE Shop_ID=?", (sid,))
    conn.commit()
    conn.close()


def db_get_shops_dropdown():
    """Lightweight (ID, Name) list used to populate dropdowns elsewhere,
    e.g. the Shop selector on the Orders panel."""
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    cur.execute("SELECT Shop_ID, Shop_Name FROM Shop ORDER BY Shop_Name")
    rows = cur.fetchall()
    conn.close()
    return rows


# ── Screen ────────────────────────────────────────────────────────


class ShopScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=NAVY)
        self._build()
        self._load()

    def _build(self):
        section_heading(self, "🏪", "Shop Management")

        box = form_box(self, "Add New Shop")
        self.name_e = labeled_entry(box, "Shop Name *", 1, 0, "e.g. Bismillah Fabrics")
        self.owner_e = labeled_entry(box, "Owner Name *", 1, 1, "e.g. Haji Farooq")
        self.phone_e = labeled_entry(box, "Phone *", 1, 2, "e.g. 0312-9876543")
        self.location_e = labeled_entry(
            box, "Location *", 2, 0, "e.g. Shop 14, Jodia Bazaar", width=220
        )
        self.city_e = labeled_entry(box, "City *", 2, 1, "e.g. Karachi")

        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.grid(row=3, column=0, columnspan=6, sticky="w", padx=12, pady=(4, 14))
        primary_btn(btn_row, "➕  Add Shop", self._add, PURPLE).pack(side="left", padx=(0, 10))
        danger_btn(btn_row, "🗑  Delete Selected", self._delete).pack(side="left")

        search_bar(self, self._search, self._load)

        cols = ("ID", "Shop Name", "Owner", "Phone", "Location", "City")
        widths = (50, 200, 150, 150, 200, 120)
        tf, self.tree = make_treeview(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=GRAY)
        self.status.pack(anchor="w", padx=16, pady=(0, 8))

    def _load(self):
        try:
            rows = db_get_shops()
        except Exception as ex:
            fill_tree(self.tree, [])
            self.status.configure(text=f"  ⚠ Could not load shops: {ex}")
            return
        fill_tree(self.tree, rows)
        if rows:
            self.status.configure(text=f"  Total shops: {len(rows)}")
        else:
            self.status.configure(
                text="  No shops found yet — add one using the form above."
            )

    def _search(self, kw):
        try:
            rows = db_get_shops(kw)
        except Exception as ex:
            fill_tree(self.tree, [])
            self.status.configure(text=f"  ⚠ Search failed: {ex}")
            return
        fill_tree(self.tree, rows)
        self.status.configure(text=f"  Search results: {len(rows)}")

    def _add(self):
        n = self.name_e.get().strip()
        own = self.owner_e.get().strip()
        ph = self.phone_e.get().strip()
        loc = self.location_e.get().strip()
        city = self.city_e.get().strip()
        if not all([n, own, ph, loc, city]):
            messagebox.showwarning("Missing Fields", "Please fill all shop fields before adding.")
            return
        try:
            db_add_shop(n, own, ph, loc, city)
            for e in (self.name_e, self.owner_e, self.phone_e, self.location_e, self.city_e):
                e.delete(0, "end")
            self._load()
            messagebox.showinfo("Success", f"Shop '{n}' added successfully!")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a shop to delete.")
            return
        sid = self.tree.item(sel[0])["values"][0]
        name = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Confirm Delete", f"Delete shop '{name}'?"):
            try:
                db_delete_shop(sid)
                self._load()
            except Exception as ex:
                messagebox.showerror(
                    "Cannot Delete", f"Shop has linked orders and cannot be deleted.\n\n{ex}"
                )