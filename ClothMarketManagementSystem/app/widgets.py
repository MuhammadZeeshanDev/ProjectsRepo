"""
Small reusable UI pieces used by every panel: styled tables, form
fields, buttons and the search bar. Keeping them here means each
panel file only has to describe its own layout, not rebuild these
from scratch.
"""

import customtkinter as ctk
from tkinter import ttk

from app.theme import ACCENT, CARD, GRAY, LIGHT, WHITE, SUCCESS, DANGER, HOVER


def make_treeview(parent, columns, widths, height=14):
    """Creates a styled ttk.Treeview table and returns (frame, tree)."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Dark.Treeview",
        background=CARD,
        foreground=WHITE,
        rowheight=30,
        fieldbackground=CARD,
        font=("Segoe UI", 10),
        borderwidth=0,
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=ACCENT,
        foreground=WHITE,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        borderwidth=0,
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", WHITE)],
    )

    frame = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
    tree = ttk.Treeview(
        frame, columns=columns, show="headings", style="Dark.Treeview", height=height
    )
    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center", stretch=True)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    return frame, tree


def fill_tree(tree, rows):
    """Clears a treeview and reloads it with fresh rows."""
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=[str(v) for v in row], tags=(tag,))
    tree.tag_configure("even", background=CARD)
    tree.tag_configure("odd", background="#0F2C3F")


def section_heading(parent, icon, title):
    """Blue title bar shown at the top of every panel."""
    bar = ctk.CTkFrame(parent, fg_color=ACCENT, corner_radius=0, height=50)
    bar.pack(fill="x")
    bar.pack_propagate(False)
    ctk.CTkLabel(
        bar, text=f"  {icon}  {title}", font=("Segoe UI", 16, "bold"), text_color=WHITE
    ).pack(side="left", padx=16, pady=12)


def labeled_entry(parent, label, row, col, placeholder="", width=200):
    """A label + text entry placed on a grid, returns the entry widget."""
    ctk.CTkLabel(parent, text=label, font=("Segoe UI", 12), text_color=LIGHT).grid(
        row=row, column=col * 2, padx=(14, 6), pady=7, sticky="e"
    )
    entry = ctk.CTkEntry(
        parent,
        width=width,
        placeholder_text=placeholder,
        font=("Segoe UI", 12),
        height=36,
        fg_color="#0B1C2C",
        border_color=ACCENT,
        text_color=WHITE,
        placeholder_text_color=GRAY,
    )
    entry.grid(row=row, column=col * 2 + 1, padx=(0, 14), pady=7, sticky="w")
    return entry


def labeled_dropdown(parent, label, row, col, values, width=200):
    """A label + dropdown placed on a grid, returns the dropdown widget."""
    ctk.CTkLabel(parent, text=label, font=("Segoe UI", 12), text_color=LIGHT).grid(
        row=row, column=col * 2, padx=(14, 6), pady=7, sticky="e"
    )
    dropdown = ctk.CTkOptionMenu(
        parent,
        values=values if values else ["—"],
        width=width,
        font=("Segoe UI", 12),
        height=36,
        fg_color=ACCENT,
        button_color=HOVER,
        dropdown_fg_color=CARD,
        text_color=WHITE,
        dropdown_text_color=WHITE,
    )
    dropdown.grid(row=row, column=col * 2 + 1, padx=(0, 14), pady=7, sticky="w")
    return dropdown


def primary_btn(parent, text, cmd, color=SUCCESS, width=170):
    hover = "#0F5C33" if color == SUCCESS else HOVER
    return ctk.CTkButton(
        parent,
        text=text,
        command=cmd,
        fg_color=color,
        hover_color=hover,
        font=("Segoe UI", 12, "bold"),
        height=38,
        width=width,
        corner_radius=8,
        text_color=WHITE,
    )


def danger_btn(parent, text, cmd, width=170):
    return ctk.CTkButton(
        parent,
        text=text,
        command=cmd,
        fg_color=DANGER,
        hover_color="#7A1E18",
        font=("Segoe UI", 12, "bold"),
        height=38,
        width=width,
        corner_radius=8,
        text_color=WHITE,
    )


def info_btn(parent, text, cmd, width=170):
    return ctk.CTkButton(
        parent,
        text=text,
        command=cmd,
        fg_color=ACCENT,
        hover_color=HOVER,
        font=("Segoe UI", 12, "bold"),
        height=38,
        width=width,
        corner_radius=8,
        text_color=WHITE,
    )


def search_bar(parent, on_search, on_clear):
    """Search entry + Search/Clear buttons, wired to the given callbacks."""
    bar = ctk.CTkFrame(parent, fg_color="transparent")
    bar.pack(fill="x", padx=16, pady=(10, 4))
    ctk.CTkLabel(bar, text="Search:", font=("Segoe UI", 12), text_color=LIGHT).pack(
        side="left", padx=(0, 6)
    )
    entry = ctk.CTkEntry(
        bar,
        width=280,
        height=36,
        font=("Segoe UI", 12),
        fg_color=CARD,
        border_color=ACCENT,
        text_color=WHITE,
        placeholder_text="Type to search...",
        placeholder_text_color=GRAY,
    )
    entry.pack(side="left", padx=(0, 8))
    entry.bind("<Return>", lambda ev: on_search(entry.get()))
    ctk.CTkButton(
        bar,
        text="🔍 Search",
        width=100,
        height=36,
        fg_color=ACCENT,
        hover_color=HOVER,
        font=("Segoe UI", 12),
        command=lambda: on_search(entry.get()),
    ).pack(side="left", padx=(0, 6))
    ctk.CTkButton(
        bar,
        text="✕ Clear",
        width=80,
        height=36,
        fg_color="#2C3E50",
        font=("Segoe UI", 12),
        command=lambda: [entry.delete(0, "end"), on_clear()],
    ).pack(side="left")
    return entry


def form_box(parent, title):
    """Card that wraps an "add new record" form."""
    box = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
    box.pack(fill="x", padx=16, pady=(0, 10))
    ctk.CTkLabel(box, text=title, font=("Segoe UI", 13, "bold"), text_color=LIGHT).grid(
        row=0, column=0, columnspan=12, sticky="w", padx=14, pady=(12, 4)
    )
    return box


def stat_card(parent, title, value, color, icon):
    """One KPI card on the dashboard (e.g. Total Orders)."""
    card = ctk.CTkFrame(parent, fg_color=color, corner_radius=14)
    card.pack(side="left", expand=True, fill="both", padx=8, pady=6)
    ctk.CTkLabel(card, text=icon, font=("Segoe UI", 28)).pack(pady=(16, 2))
    ctk.CTkLabel(card, text=value, font=("Segoe UI", 26, "bold"), text_color=WHITE).pack()
    ctk.CTkLabel(card, text=title, font=("Segoe UI", 11), text_color="#D0E8FF").pack(
        pady=(2, 16)
    )
