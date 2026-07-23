import os
import tkinter as tk
from tkinter import ttk, messagebox
from .dashboard import DashboardView
from .products import ProductsView
from .sales import SalesView
from .customers import CustomersView
from .reports import ReportsView


class MainWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.root.title("AD_Coder - Firecracker Inventory Management")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 600)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.dashboard = DashboardView(self.notebook, db)
        self.products = ProductsView(self.notebook, db)
        self.sales = SalesView(self.notebook, db)
        self.customers = CustomersView(self.notebook, db)
        self.reports = ReportsView(self.notebook, db)

        self.notebook.add(self.dashboard.frame, text=" Dashboard ")
        self.notebook.add(self.products.frame, text=" Products ")
        self.notebook.add(self.sales.frame, text=" Sales / Invoicing ")
        self.notebook.add(self.customers.frame, text=" Customers ")
        self.notebook.add(self.reports.frame, text=" Reports ")

        self.create_menu()

    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text").strip()
        if tab_text == "Dashboard":
            self.dashboard.refresh()
        elif tab_text == "Products":
            self.products.load_products()
        elif tab_text == "Sales / Invoicing":
            self.sales.load_product_list()
            self.sales.load_customers()
        elif tab_text == "Customers":
            self.customers.load_customers()
        elif tab_text == "Reports":
            self.reports.load_sales_report("today")
            self.reports.refresh_expenses()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Backup Database", command=self.backup_db)
        file_menu.add_command(label="Export Database", command=self.export_db)
        file_menu.add_command(label="Import Database", command=self.import_db)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dashboard", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="Products", command=lambda: self.notebook.select(1))
        view_menu.add_command(label="Sales", command=lambda: self.notebook.select(2))
        view_menu.add_command(label="Customers", command=lambda: self.notebook.select(3))
        view_menu.add_command(label="Reports", command=lambda: self.notebook.select(4))

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def backup_db(self):
        import shutil
        from datetime import datetime
        src = self.db.db_path
        backup_dir = os.path.join(os.path.dirname(src), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(backup_dir, f"backup_{ts}.db")
        try:
            shutil.copy2(src, dst)
            messagebox.showinfo("Backup", f"Database backed up to:\n{dst}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")

    def export_db(self):
        from tkinter import filedialog
        import shutil
        dst = filedialog.asksaveasfilename(
            title="Export Database",
            initialfile="ad_coder_export.db",
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        if not dst:
            return
        try:
            shutil.copy2(self.db.db_path, dst)
            messagebox.showinfo("Export", f"Database exported successfully to:\n{dst}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def import_db(self):
        from tkinter import filedialog
        import shutil
        import sqlite3
        src = filedialog.askopenfilename(
            title="Import Database",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        if not src:
            return
        if messagebox.askyesno("Confirm Import", "Importing a database will overwrite your current database. Do you want to proceed?"):
            try:
                self.db.close()
                shutil.copy2(src, self.db.db_path)
                
                # Reopen connection
                self.db.conn = sqlite3.connect(self.db.db_path)
                self.db.conn.row_factory = sqlite3.Row
                self.db.conn.execute("PRAGMA foreign_keys = ON")
                
                # Reload active view data
                self.dashboard.db = self.db
                self.products.db = self.db
                self.sales.db = self.db
                self.customers.db = self.db
                self.reports.db = self.db
                
                self.dashboard.refresh()
                self.products.load_products()
                self.sales.load_customers()
                self.sales.load_product_list()
                self.customers.load_customers()
                
                messagebox.showinfo("Import", "Database imported and views refreshed successfully!")
            except Exception as e:
                # Attempt to reopen original DB in case of copy/corruption failure
                try:
                    self.db.conn = sqlite3.connect(self.db.db_path)
                    self.db.conn.row_factory = sqlite3.Row
                    self.db.conn.execute("PRAGMA foreign_keys = ON")
                except:
                    pass
                messagebox.showerror("Error", f"Import failed: {e}")

    def show_about(self):
        messagebox.showinfo("About AD_Coder",
            "AD_Coder v1.0\n\n"
            "Firecracker Inventory Management System\n\n"
            "Built with Python & Tkinter\n"
            "Compatible with Windows, Mac & Linux")
