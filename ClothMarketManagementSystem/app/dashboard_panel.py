"""
Dashboard panel: the landing screen after login. Shows KPI cards,
a table of recent orders, and two charts built from live order data
- a bar chart of revenue by fabric, and a donut chart of payment
status. Both are rendered with matplotlib and embedded straight into
the CustomTkinter window.
"""

import customtkinter as ctk
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.config import get_conn
from app.theme import NAVY, CARD, LIGHT, GRAY, WHITE, GOLD, SUCCESS, DANGER, TEAL, CHART_COLORS
from app.widgets import section_heading, make_treeview, fill_tree, stat_card, search_bar

# ── Database queries ─────────────────────────────────────────────


def db_get_stats():
    conn = get_conn()
    if not conn:
        return 0, 0, 0.0, 0, 0
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Orders")
    orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Customer")
    customers = cur.fetchone()[0]
    cur.execute("SELECT ISNULL(SUM(Total_Amount), 0) FROM Orders")
    revenue = float(cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM Orders WHERE Payment_Status='Unpaid'")
    unpaid = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Supplier")
    suppliers = cur.fetchone()[0]
    conn.close()
    return orders, customers, revenue, unpaid, suppliers


def db_get_top_fabrics(limit=5):
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT TOP {limit} f.Fabric_Name, SUM(o.Total_Amount) AS Revenue
        FROM Orders o
        INNER JOIN Fabric f ON o.Fabric_ID = f.Fabric_ID
        GROUP BY f.Fabric_Name
        ORDER BY Revenue DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def db_get_recent_orders(limit=5):
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT TOP {limit}
            o.Order_ID, c.Customer_Name, f.Fabric_Name, o.Total_Amount, o.Payment_Status
        FROM Orders o
        INNER JOIN Customer c ON o.Customer_ID = c.Customer_ID
        INNER JOIN Fabric   f ON o.Fabric_ID   = f.Fabric_ID
        ORDER BY o.Order_ID DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def db_quick_search(keyword):
    """Searches Customer, Supplier, Fabric and Shop by name in one go,
    for the Dashboard's quick-search bar. Returns (Type, Name, Detail) rows."""
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    kw = f"%{keyword}%"
    results = []

    cur.execute("SELECT Customer_Name, City FROM Customer WHERE Customer_Name LIKE ?", (kw,))
    results += [("Customer", r[0], r[1]) for r in cur.fetchall()]

    cur.execute("SELECT Supplier_Name, City FROM Supplier WHERE Supplier_Name LIKE ?", (kw,))
    results += [("Supplier", r[0], r[1]) for r in cur.fetchall()]

    cur.execute("SELECT Fabric_Name, Category FROM Fabric WHERE Fabric_Name LIKE ?", (kw,))
    results += [("Fabric", r[0], r[1]) for r in cur.fetchall()]

    cur.execute("SELECT Shop_Name, City FROM Shop WHERE Shop_Name LIKE ?", (kw,))
    results += [("Shop", r[0], r[1]) for r in cur.fetchall()]

    conn.close()
    return results


def db_get_payment_breakdown():
    """Returns [(status, count), ...] used for the payment status donut chart."""
    conn = get_conn()
    if not conn:
        return []
    cur = conn.cursor()
    cur.execute(
        "SELECT Payment_Status, COUNT(*) FROM Orders GROUP BY Payment_Status ORDER BY Payment_Status"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ── Chart helpers ────────────────────────────────────────────────

STATUS_COLORS = {"Paid": SUCCESS, "Unpaid": DANGER, "Partial": GOLD}


def _style_axes(fig, ax):
    fig.patch.set_facecolor(CARD)
    ax.set_facecolor(CARD)
    ax.tick_params(colors=LIGHT, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#1A3A52")


def build_revenue_bar_chart(parent, data):
    """Horizontal bar chart comparing revenue across the top fabrics."""
    fig = Figure(figsize=(4.6, 3.1), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(fig, ax)

    if data:
        names = [row[0] for row in reversed(data)]
        values = [float(row[1]) for row in reversed(data)]
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(names))]
        ax.barh(names, values, color=colors, height=0.55)
        ax.set_xlabel("Revenue (PKR)", color=LIGHT, fontsize=9)
        for i, v in enumerate(values):
            ax.text(v, i, f"  {v:,.0f}", va="center", color=WHITE, fontsize=8)
    else:
        ax.text(0.5, 0.5, "No order data yet", ha="center", va="center", color=GRAY, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


def build_payment_donut_chart(parent, data):
    """Donut chart showing the share of orders per payment status."""
    fig = Figure(figsize=(4.6, 3.1), dpi=100)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(CARD)
    ax.set_facecolor(CARD)

    if data:
        labels = [row[0] for row in data]
        values = [row[1] for row in data]
        colors = [STATUS_COLORS.get(label, TEAL) for label in labels]
        wedges, _texts, autotexts = ax.pie(
            values,
            labels=None,
            colors=colors,
            autopct=lambda p: f"{p:.0f}%" if p > 0 else "",
            pctdistance=0.8,
            startangle=90,
            wedgeprops=dict(width=0.42, edgecolor=CARD),
        )
        for t in autotexts:
            t.set_color(WHITE)
            t.set_fontsize(8)
        ax.legend(
            wedges,
            [f"{l} ({v})" for l, v in zip(labels, values)],
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            fontsize=8,
            labelcolor=LIGHT,
            frameon=False,
        )
    else:
        ax.text(0.5, 0.5, "No order data yet", ha="center", va="center", color=GRAY, transform=ax.transAxes)

    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


# ── Screen ────────────────────────────────────────────────────────


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=NAVY)
        self._build()

    def _build(self):
        section_heading(self, "📊", "Dashboard  —  Cloth Market Overview")

        search_bar(self, self._quick_search, self._hide_search_results)

        self.search_frame = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10, height=170)
        self.search_frame.pack(fill="x", padx=16, pady=(0, 10))
        self.search_frame.pack_propagate(False)
        cols = ("Type", "Name", "Detail")
        widths = (100, 240, 200)
        stf, self.search_tree = make_treeview(self.search_frame, cols, widths, height=4)
        stf.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.search_status = ctk.CTkLabel(
            self.search_frame,
            text="  Search across Customers, Suppliers, Fabrics and Shops using the bar above.",
            font=("Segoe UI", 11),
            text_color=GRAY,
        )
        self.search_status.pack(anchor="w", padx=16, pady=(4, 8))

        try:
            orders, customers, revenue, unpaid, suppliers = db_get_stats()
        except Exception:
            orders = customers = revenue = unpaid = suppliers = 0

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=16, pady=14)
        stat_card(cards, "Total Orders", str(orders), "#1A5F8A", "📦")
        stat_card(cards, "Customers", str(customers), SUCCESS, "👥")
        stat_card(cards, "Revenue (PKR)", f"{revenue:,.0f}", GOLD, "💰")
        stat_card(cards, "Unpaid Orders", str(unpaid), DANGER, "⚠️")
        stat_card(cards, "Suppliers", str(suppliers), TEAL, "🏭")

        # Recent orders + payment status chart
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=1)
        row1.rowconfigure(0, weight=1)

        left = ctk.CTkFrame(row1, fg_color=CARD, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(left, text="🕐  Recent Orders", font=("Segoe UI", 13, "bold"), text_color=LIGHT).pack(
            anchor="w", padx=14, pady=(12, 6)
        )
        cols = ("ID", "Customer", "Fabric", "Total (PKR)", "Status")
        widths = (50, 160, 120, 110, 80)
        tf, self.recent_tree = make_treeview(left, cols, widths, height=7)
        tf.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        try:
            fill_tree(self.recent_tree, db_get_recent_orders())
        except Exception:
            pass

        right = ctk.CTkFrame(row1, fg_color=CARD, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(
            right, text="💳  Orders by Payment Status", font=("Segoe UI", 13, "bold"), text_color=LIGHT
        ).pack(anchor="w", padx=14, pady=(12, 6))
        try:
            chart_widget = build_payment_donut_chart(right, db_get_payment_breakdown())
        except Exception:
            chart_widget = ctk.CTkLabel(right, text="Chart unavailable", text_color=GRAY)
        chart_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Revenue by fabric chart, full width
        row2 = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        row2.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        ctk.CTkLabel(
            row2, text="🧶  Top Fabrics by Revenue", font=("Segoe UI", 13, "bold"), text_color=LIGHT
        ).pack(anchor="w", padx=14, pady=(12, 6))
        try:
            bar_widget = build_revenue_bar_chart(row2, db_get_top_fabrics())
        except Exception:
            bar_widget = ctk.CTkLabel(row2, text="Chart unavailable", text_color=GRAY)
        bar_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        info = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10, height=44)
        info.pack(fill="x", padx=16, pady=(0, 10))
        info.pack_propagate(False)
        ctk.CTkLabel(
            info,
            text="  🧵  Wholesale Cloth Market Management System  |  "
            "Use the sidebar to manage Customers, Suppliers, Fabrics, Shops and Orders",
            font=("Segoe UI", 11),
            text_color=GRAY,
        ).pack(side="left", padx=10, pady=10)

    def _quick_search(self, kw):
        kw = kw.strip()
        if not kw:
            self._hide_search_results()
            return
        try:
            rows = db_quick_search(kw)
        except Exception as ex:
            fill_tree(self.search_tree, [])
            self.search_status.configure(text=f"  ⚠ Search failed: {ex}")
            return
        fill_tree(self.search_tree, rows)
        self.search_status.configure(
            text=f"  {len(rows)} result(s) for '{kw}'"
            if rows
            else f"  No matches found for '{kw}'"
        )

    def _hide_search_results(self):
        fill_tree(self.search_tree, [])
        self.search_status.configure(
            text="  Search across Customers, Suppliers, Fabrics and Shops using the bar above."
        )