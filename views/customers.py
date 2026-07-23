import os
import tkinter as tk
from tkinter import ttk, messagebox


class CustomersView:
    def __init__(self, parent, db):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.search_var = tk.StringVar()
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(toolbar, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Search", command=self.load_customers).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Clear", command=lambda: [self.search_var.set(""), self.load_customers()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="+ Add Customer", command=self.add_customer_dialog).pack(side=tk.RIGHT, padx=5)

        columns = ("ID", "Name", "Phone", "Email", "Address", "Invoice")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.column("ID", width=40)
        self.tree.column("Name", width=150)
        self.tree.column("Address", width=180)
        self.tree.column("Invoice", width=250)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.tree.bind("<Double-1>", lambda e: self.edit_customer_dialog())

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="Edit Selected", command=self.edit_customer_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Selected Invoice", command=self.open_invoice).pack(side=tk.LEFT, padx=5)

    def load_customers(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        customers = self.db.search_customers(self.search_var.get())
        for c in customers:
            invoices = self.db.conn.execute("SELECT invoice_no FROM invoices WHERE customer_id=?", (c["id"],)).fetchall()
            inv_str = ", ".join([row["invoice_no"] for row in invoices])
            self.tree.insert("", tk.END, values=(
                c["id"], c["name"], c["phone"] or "", c["email"] or "", c["address"] or "", inv_str
            ))

    def add_customer_dialog(self):
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Customer")
        dialog.geometry("450x300")
        dialog.transient(self.frame)
        dialog.grab_set()

        entries = {}
        fields = [("Name", "name"), ("Phone", "phone"), ("Email", "email"), ("Address", "address")]

        for i, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            entries[key] = ttk.Entry(dialog, width=30)
            entries[key].grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)

        def save():
            data = {k: v.get() for k, v in entries.items()}
            if not data["name"]:
                messagebox.showerror("Error", "Name is required")
                return
            try:
                self.db.add_customer(data["name"], data["phone"], data["email"], data["address"])
                self.load_customers()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def edit_customer_dialog(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a customer to edit")
            return
        item = self.tree.item(sel[0])
        cid = item["values"][0]
        cust = self.db.conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
        if not cust:
            return

        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Edit Customer - {cust['name']}")
        dialog.geometry("450x300")
        dialog.transient(self.frame)
        dialog.grab_set()

        entries = {}
        fields = [("Name", "name", cust["name"]), ("Phone", "phone", cust["phone"] or ""),
                  ("Email", "email", cust["email"] or ""), ("Address", "address", cust["address"] or "")]

        for i, (label, key, default) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            entries[key] = ttk.Entry(dialog, width=30)
            entries[key].insert(0, default)
            entries[key].grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)

        def save():
            data = {k: v.get() for k, v in entries.items()}
            if not data["name"]:
                messagebox.showerror("Error", "Name is required")
                return
            try:
                self.db.update_customer(cid, data["name"], data["phone"], data["email"], data["address"])
                self.load_customers()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def delete_customer(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a customer to delete")
            return
        item = self.tree.item(sel[0])
        cid = item["values"][0]
        name = item["values"][1]
        if messagebox.askyesno("Confirm Delete", f"Delete customer '{name}'?"):
            self.db.delete_customer(cid)
            self.load_customers()

    def open_invoice(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a customer first")
            return
        item = self.tree.item(sel[0])
        cid = item["values"][0]
        
        invoices = self.db.conn.execute("SELECT invoice_no FROM invoices WHERE customer_id=?", (cid,)).fetchall()
        if not invoices:
            messagebox.showinfo("No Invoices", "No invoices found for this customer.")
            return
        
        from utils.invoice_helper import show_invoice_receipt
        if len(invoices) == 1:
            inv_no = invoices[0]["invoice_no"]
            show_invoice_receipt(self.frame, self.db, inv_no)
        else:
            # Show dialog to pick which invoice to open
            dialog = tk.Toplevel(self.frame)
            dialog.title("Select Invoice")
            dialog.geometry("320x300")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Select an invoice to open:").pack(pady=10)
            
            listbox = tk.Listbox(dialog, selectmode=tk.SINGLE)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            for inv in invoices:
                listbox.insert(tk.END, inv["invoice_no"])
                
            def on_open():
                sel_idx = listbox.curselection()
                if not sel_idx:
                    return
                inv_no = listbox.get(sel_idx[0])
                show_invoice_receipt(self.frame, self.db, inv_no)
                dialog.destroy()
                
            ttk.Button(dialog, text="Open", command=on_open).pack(pady=10)
