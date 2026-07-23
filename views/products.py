import tkinter as tk
from tkinter import ttk, messagebox


class ProductsView:
    def __init__(self, parent, db):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(toolbar, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Search", command=self.load_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=5)

        ttk.Label(toolbar, text="Category:").pack(side=tk.LEFT, padx=(20, 5))
        self.cat_combo = ttk.Combobox(toolbar, textvariable=self.category_var, state="readonly", width=25)
        self.cat_combo.pack(side=tk.LEFT, padx=5)
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.load_products())

        ttk.Button(toolbar, text="+ Add Product", command=self.add_product_dialog).pack(side=tk.RIGHT, padx=5)

        columns = ("ID", "Code", "Name", "Category", "Unit", "Price", "Discount %")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_tree(c))
            self.tree.column(col, width=100)

        self.tree.column("ID", width=40)
        self.tree.column("Name", width=250)
        self.tree.column("Code", width=60)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.tree.bind("<Double-1>", lambda e: self.edit_product_dialog())

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="Edit Selected", command=self.edit_product_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_product).pack(side=tk.LEFT, padx=5)

    def clear_search(self):
        self.search_var.set("")
        self.category_var.set("")
        self.load_products()

    def sort_tree(self, col):
        pass

    def load_products(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        cat_combo_values = ["All Categories"]
        cat_combo_values.extend([r["name"] for r in self.db.get_categories()])
        self.cat_combo["values"] = cat_combo_values
        if not self.category_var.get():
            self.category_var.set("All Categories")

        cat_id = None
        if self.category_var.get() and self.category_var.get() != "All Categories":
            for r in self.db.get_categories():
                if r["name"] == self.category_var.get():
                    cat_id = r["id"]
                    break

        products = self.db.search_products(self.search_var.get(), cat_id)
        for p in products:
            self.tree.insert("", tk.END, values=(
                p["id"], p["code"] or "", p["name"], p["category_name"] or "",
                p["unit"], f"₹{p['sale_price']:.2f}" if p["sale_price"] else "₹0.00",
                f"{p['discount_percent']:.0f}%" if p["discount_percent"] else "0%"
            ))

    def add_product_dialog(self):
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Product")
        dialog.geometry("400x310")
        dialog.transient(self.frame)
        dialog.grab_set()

        entries = {}
        fields = [
            ("Product Name", "name"),
            ("Code", "code"),
            ("Category", "category"),
            ("Unit", "unit"),
            ("Sale Price (₹)", "sale_price"),
            ("Discount %", "discount_percent"),
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            if key == "category":
                var = tk.StringVar()
                cat_vals = [r["name"] for r in self.db.get_categories()]
                widget = ttk.Combobox(dialog, textvariable=var, values=cat_vals, state="readonly", width=27)
                if cat_vals:
                    var.set(cat_vals[0])
                entries[key] = var
            else:
                widget = ttk.Entry(dialog, width=30)
                if key in ("sale_price", "discount_percent"):
                    widget.insert(0, "0")
                elif key == "unit":
                    widget.insert(0, "PCS")
                entries[key] = widget
            widget.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)

        def save():
            data = {k: v.get() if isinstance(v, tk.StringVar) else v.get() for k, v in entries.items()}
            if not data["name"]:
                messagebox.showerror("Error", "Product name is required")
                return
            cat_id = None
            if data["category"]:
                for r in self.db.get_categories():
                    if r["name"] == data["category"]:
                        cat_id = r["id"]
                        break
            try:
                self.db.add_product(
                    data["name"], data["code"], cat_id, data["unit"],
                    float(data["sale_price"] or 0), float(data["discount_percent"] or 0)
                )
                self.load_products()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def edit_product_dialog(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a product to edit")
            return
        item = self.tree.item(sel[0])
        pid = item["values"][0]
        prod = self.db.conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if not prod:
            return

        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Edit Product - {prod['name']}")
        dialog.geometry("400x310")
        dialog.transient(self.frame)
        dialog.grab_set()

        entries = {}
        fields = [
            ("Product Name", "name", prod["name"]),
            ("Code", "code", prod["code"] or ""),
            ("Category", "category", ""),
            ("Unit", "unit", prod["unit"]),
            ("Sale Price (₹)", "sale_price", str(prod["sale_price"])),
            ("Discount %", "discount_percent", str(prod["discount_percent"])),
        ]

        for i, (label, key, default) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            if key == "category":
                var = tk.StringVar()
                cat_vals = [r["name"] for r in self.db.get_categories()]
                widget = ttk.Combobox(dialog, textvariable=var, values=cat_vals, state="readonly", width=27)
                for r in self.db.get_categories():
                    if r["id"] == prod["category_id"]:
                        var.set(r["name"])
                        break
                if not var.get() and cat_vals:
                    var.set(cat_vals[0])
                entries[key] = var
            else:
                widget = ttk.Entry(dialog, width=30)
                widget.insert(0, default)
                entries[key] = widget
            widget.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)

        def save():
            data = {k: v.get() if isinstance(v, tk.StringVar) else v.get() for k, v in entries.items()}
            if not data["name"]:
                messagebox.showerror("Error", "Product name is required")
                return
            cat_id = None
            if data["category"]:
                for r in self.db.get_categories():
                    if r["name"] == data["category"]:
                        cat_id = r["id"]
                        break
            try:
                self.db.update_product(
                    pid, data["name"], data["code"], cat_id, data["unit"],
                    float(data["sale_price"] or 0), float(data["discount_percent"] or 0)
                )
                self.load_products()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def delete_product(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a product to delete")
            return
        item = self.tree.item(sel[0])
        pid = item["values"][0]
        name = item["values"][2]
        if messagebox.askyesno("Confirm Delete", f"Delete product '{name}'?"):
            self.db.delete_product(pid)
            self.load_products()
