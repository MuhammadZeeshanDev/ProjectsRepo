"""
Login window shown before the main application opens.

This is a simple hard-coded check rather than a database-backed user
table, since access control was outside the scope of this project.
"""

import customtkinter as ctk

from app.theme import NAVY, CARD, WHITE, LIGHT, GRAY, ACCENT

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cloth Market Management System — Login")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=NAVY)
        self._build()

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=18)
        card.pack(expand=True, padx=36, pady=36, fill="both")

        ctk.CTkLabel(card, text="🧵", font=("Segoe UI", 52)).pack(pady=(28, 4))
        ctk.CTkLabel(card, text="Cloth Market System", font=("Segoe UI", 20, "bold"), text_color=WHITE).pack()
        ctk.CTkLabel(
            card, text="Wholesale Management Portal", font=("Segoe UI", 12), text_color=GRAY
        ).pack(pady=(4, 26))

        ctk.CTkLabel(card, text="Username", font=("Segoe UI", 12), text_color=LIGHT, anchor="w").pack(
            fill="x", padx=36
        )
        self.user = ctk.CTkEntry(
            card,
            placeholder_text="Enter username",
            height=42,
            width=300,
            font=("Segoe UI", 13),
            fg_color=NAVY,
            border_color=ACCENT,
            text_color=WHITE,
        )
        self.user.pack(padx=36, pady=(4, 12))

        ctk.CTkLabel(card, text="Password", font=("Segoe UI", 12), text_color=LIGHT, anchor="w").pack(
            fill="x", padx=36
        )
        self.pwd = ctk.CTkEntry(
            card,
            placeholder_text="Enter password",
            show="●",
            height=42,
            width=300,
            font=("Segoe UI", 13),
            fg_color=NAVY,
            border_color=ACCENT,
            text_color=WHITE,
        )
        self.pwd.pack(padx=36, pady=(4, 6))

        self.err = ctk.CTkLabel(card, text="", text_color="#E74C3C", font=("Segoe UI", 12))
        self.err.pack(pady=(4, 8))

        ctk.CTkButton(
            card,
            text="Login →",
            height=44,
            width=300,
            font=("Segoe UI", 14, "bold"),
            fg_color=ACCENT,
            hover_color="#155D8A",
            text_color=WHITE,
            command=self._login,
        ).pack(padx=36, pady=(0, 6))

        ctk.CTkLabel(
            card, text="NED University  |  CT-261 DBMS Project", font=("Segoe UI", 10), text_color="#2A4A5A"
        ).pack(pady=(14, 20))

        self.bind("<Return>", lambda e: self._login())
        self.user.focus()

    def _login(self):
        u = self.user.get().strip()
        p = self.pwd.get().strip()
        if u == DEFAULT_USERNAME and p == DEFAULT_PASSWORD:
            self.destroy()
            # Imported here to avoid a circular import with main_window.
            from app.main_window import MainApp

            MainApp().mainloop()
        else:
            self.err.configure(text="❌  Invalid username or password")
            self.pwd.delete(0, "end")
