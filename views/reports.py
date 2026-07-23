import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta


class ReportsView:
    def __init__(self, parent, db):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sales_tab = ttk.Frame(notebook)
        self.expiry_tab = ttk.Frame(notebook)

        notebook.add(self.sales_tab, text="Sales Report")
        notebook.add(self.expiry_tab, text="Expense Report")

        self.setup_sales_tab()
        self.setup_expense_tab()

    def setup_sales_tab(self):
        btn_frame = ttk.Frame(self.sales_tab)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Today's Sales", command=lambda: self.load_sales_report("today")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="This Week", command=lambda: self.load_sales_report("week")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="This Month", command=lambda: self.load_sales_report("month")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="All Sales", command=lambda: self.load_sales_report("all")).pack(side=tk.LEFT, padx=5)

        columns = ("Invoice", "Customer", "Date", "Items", "Subtotal", "Discount", "Total", "Payment")
        self.sales_tree = ttk.Treeview(self.sales_tab, columns=columns, show="headings", height=15)
        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=100)

        scroll = ttk.Scrollbar(self.sales_tab, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scroll.set)
        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        self.sales_summary = ttk.Label(self.sales_tab, text="", font=("Arial", 12, "bold"))
        self.sales_summary.pack(pady=10)

        self.load_sales_report("today")

    def load_sales_report(self, period):
        for row in self.sales_tree.get_children():
            self.sales_tree.delete(row)

        query = "SELECT i.*, c.name as customer_name FROM invoices i LEFT JOIN customers c ON i.customer_id = c.id"
        params = []

        today = datetime.now().strftime("%Y-%m-%d")

        if period == "today":
            query += " WHERE date(i.created_at) = ?"
            params.append(today)
        elif period == "week":
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            query += " WHERE date(i.created_at) >= ?"
            params.append(week_ago)
        elif period == "month":
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            query += " WHERE date(i.created_at) >= ?"
            params.append(month_ago)

        query += " ORDER BY i.created_at DESC"

        invoices = self.db.conn.execute(query, params).fetchall()
        total_sum = 0
        for inv in invoices:
            item_count = self.db.conn.execute("SELECT COUNT(*) FROM invoice_items WHERE invoice_id=?", (inv["id"],)).fetchone()[0]
            self.sales_tree.insert("", tk.END, values=(
                inv["invoice_no"], inv["customer_name"] or "Walk-in",
                inv["invoice_date"][:10] if inv["invoice_date"] else "",
                item_count,
                f"₹{inv['subtotal']:.2f}", f"₹{inv['discount_total']:.2f}",
                f"₹{inv['grand_total']:.2f}", inv["payment_mode"]
            ))
            total_sum += inv["grand_total"]

        self.sales_summary.config(text=f"Total Sales: ₹{total_sum:.2f} | Invoices: {len(invoices)}")

    def setup_expense_tab(self):
        form_frame = ttk.Frame(self.expiry_tab)
        form_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Label(form_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.exp_cat_entry = ttk.Entry(form_frame, width=20)
        self.exp_cat_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Description:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.exp_desc_entry = ttk.Entry(form_frame, width=25)
        self.exp_desc_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Amount:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.exp_amt_entry = ttk.Entry(form_frame, width=15)
        self.exp_amt_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(form_frame, text="Add Expense", command=self.add_expense).grid(row=0, column=6, padx=10)

        columns = ("ID", "Category", "Description", "Amount", "Date")
        self.exp_tree = ttk.Treeview(self.expiry_tab, columns=columns, show="headings", height=12)
        for col in columns:
            self.exp_tree.heading(col, text=col)
            self.exp_tree.column(col, width=120)
        self.exp_tree.column("Description", width=250)

        scroll = ttk.Scrollbar(self.expiry_tab, orient=tk.VERTICAL, command=self.exp_tree.yview)
        self.exp_tree.configure(yscrollcommand=scroll.set)
        self.exp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        self.exp_summary = ttk.Label(self.expiry_tab, text="", font=("Arial", 12, "bold"))
        self.exp_summary.pack(pady=10)

        self.refresh_expenses()

    def add_expense(self):
        category = self.exp_cat_entry.get()
        description = self.exp_desc_entry.get()
        try:
            amount = float(self.exp_amt_entry.get() or 0)
        except:
            messagebox.showerror("Error", "Invalid amount")
            return

        if amount <= 0:
            messagebox.showerror("Error", "Amount must be > 0")
            return

        try:
            self.db.conn.execute(
                "INSERT INTO expenses (category, description, amount) VALUES (?, ?, ?)",
                (category, description, amount)
            )
            self.db.conn.commit()
            self.exp_cat_entry.delete(0, tk.END)
            self.exp_desc_entry.delete(0, tk.END)
            self.exp_amt_entry.delete(0, tk.END)
            self.refresh_expenses()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_expenses(self):
        for row in self.exp_tree.get_children():
            self.exp_tree.delete(row)

        expenses = self.db.conn.execute("SELECT * FROM expenses ORDER BY created_at DESC").fetchall()
        total = 0
        for e in expenses:
            self.exp_tree.insert("", tk.END, values=(
                e["id"], e["category"] or "", e["description"] or "",
                f"₹{e['amount']:.2f}", e["expense_date"][:10] if e["expense_date"] else ""
            ))
            total += e["amount"]

        self.exp_summary.config(text=f"Total Expenses: ₹{total:.2f}")
