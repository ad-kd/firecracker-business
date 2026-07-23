import tkinter as tk
from tkinter import ttk
from datetime import datetime


class DashboardView:
    def __init__(self, parent, db):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        header = ttk.Frame(self.frame)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        ttk.Label(header, text="AD_Coder", font=("Arial", 24, "bold")).pack(anchor=tk.W)
        ttk.Label(header, text="Firecracker Inventory Management System", font=("Arial", 12)).pack(anchor=tk.W)

        self.stats_frame = ttk.Frame(self.frame)
        self.stats_frame.pack(fill=tk.X, padx=20, pady=20)

        self.refresh_btn = ttk.Button(self.frame, text="Refresh Dashboard", command=self.refresh)
        self.refresh_btn.pack(pady=5)

        self.refresh()

    def refresh(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()

        stats = self.db.get_dashboard_stats()

        cards = [
            ("Total Products", str(stats["total_products"]), "#2ecc71"),
            ("Total Customers", str(stats["total_customers"]), "#3498db"),
            ("Today's Sales (₹)", f"₹{stats['today_sales']:.2f}", "#9b59b6"),
        ]

        for i, (title, value, color) in enumerate(cards):
            card = tk.Frame(self.stats_frame, bg=color, padx=20, pady=20)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            self.stats_frame.columnconfigure(i, weight=1)

            tk.Label(card, text=title, fg="white", bg=color, font=("Arial", 12, "bold")).pack()
            tk.Label(card, text=value, fg="white", bg=color, font=("Arial", 28, "bold")).pack(pady=10)

        recent_frame = ttk.LabelFrame(self.frame, text="Recent Transactions", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("Invoice", "Customer", "Date", "Amount")
        tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        invoices = self.db.get_invoices(limit=20)
        for inv in invoices:
            tree.insert("", tk.END, values=(
                inv["invoice_no"],
                inv["customer_name"] or "Walk-in",
                inv["invoice_date"][:10] if inv["invoice_date"] else "",
                f"₹{inv['grand_total']:.2f}"
            ))
