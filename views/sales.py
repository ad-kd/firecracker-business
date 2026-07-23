import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import tempfile
from fpdf import FPDF


class SalesView:
    def __init__(self, parent, db):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.cart = []
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=2)
        paned.add(right, weight=3)

        product_frame = ttk.LabelFrame(left, text="Select Products", padding=10)
        product_frame.pack(fill=tk.BOTH, expand=True)

        search_frame = ttk.Frame(product_frame)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Search", command=self.load_product_list).pack(side=tk.LEFT)
        self.search_entry.bind("<Return>", lambda e: self.load_product_list())

        columns = ("ID", "Name", "Price")
        self.prod_tree = ttk.Treeview(product_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.prod_tree.heading(col, text=col)
            self.prod_tree.column(col, width=80)
        self.prod_tree.column("Name", width=200)
        self.prod_tree.column("Price", width=80)

        scroll = ttk.Scrollbar(product_frame, orient=tk.VERTICAL, command=self.prod_tree.yview)
        self.prod_tree.configure(yscrollcommand=scroll.set)
        self.prod_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.prod_tree.bind("<Double-1>", lambda e: self.add_to_cart())
        self.prod_tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.prod_tree.bind("<B1-Motion>", self.on_drag_motion)
        self.prod_tree.bind("<ButtonRelease-1>", self.on_drag_release)

        btn_frame = ttk.Frame(product_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add to Cart >>", command=self.add_to_cart).pack()

        self.load_product_list()

        cart_frame = ttk.LabelFrame(right, text="Shopping Cart", padding=10)
        cart_frame.pack(fill=tk.BOTH, expand=True)

        cart_columns = ("Product", "Qty", "Price", "Disc%", "Total")
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=12)
        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=100)
        self.cart_tree.column("Product", width=200)
        self.cart_tree.pack(fill=tk.BOTH, expand=True)

        cart_btn_frame = ttk.Frame(cart_frame)
        cart_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(cart_btn_frame, text="Remove Selected", command=self.remove_from_cart).pack(side=tk.LEFT, padx=5)
        ttk.Button(cart_btn_frame, text="Clear Cart", command=self.clear_cart).pack(side=tk.LEFT, padx=5)

        total_frame = ttk.Frame(cart_frame)
        total_frame.pack(fill=tk.X, pady=5)
        
        self.total_items_label = ttk.Label(total_frame, text="Total Items: 0", font=("Arial", 11))
        self.total_items_label.pack(side=tk.LEFT, padx=10)

        summary_frame = ttk.Frame(total_frame)
        summary_frame.pack(side=tk.RIGHT, padx=10)

        # Row 0: Subtotal
        ttk.Label(summary_frame, text="Subtotal:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.E, padx=5, pady=2)
        self.subtotal_label = ttk.Label(summary_frame, text="₹0.00", font=("Arial", 11, "bold"))
        self.subtotal_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        # Row 1: Discount %
        ttk.Label(summary_frame, text="Discount (%):", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.E, padx=5, pady=2)
        self.cart_discount_var = tk.StringVar(value="0")
        self.cart_discount_entry = ttk.Entry(summary_frame, textvariable=self.cart_discount_var, width=8)
        self.cart_discount_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Row 2: Total to Pay
        ttk.Label(summary_frame, text="Total to Pay:", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.E, padx=5, pady=2)
        self.total_label = ttk.Label(summary_frame, text="₹0.00", font=("Arial", 14, "bold"), foreground="green")
        self.total_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        # Bind discount entry change
        self.cart_discount_var.trace_add("write", lambda *args: self.calculate_totals())

        checkout_frame = ttk.LabelFrame(right, text="Checkout", padding=10)
        checkout_frame.pack(fill=tk.X, pady=10)

        cust_frame = ttk.Frame(checkout_frame)
        cust_frame.pack(fill=tk.X, pady=5)
        ttk.Label(cust_frame, text="Customer:").pack(side=tk.LEFT)
        self.customer_combo = ttk.Combobox(cust_frame, width=30, state="normal")
        self.customer_combo.pack(side=tk.LEFT, padx=5)
        self.load_customers()
        ttk.Button(cust_frame, text="+ New", command=self.new_customer_dialog).pack(side=tk.LEFT, padx=5)

        pay_frame = ttk.Frame(checkout_frame)
        pay_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pay_frame, text="Payment:").pack(side=tk.LEFT)
        self.payment_var = tk.StringVar(value="CASH")
        ttk.Combobox(pay_frame, textvariable=self.payment_var, values=("CASH", "CARD", "UPI", "CREDIT"), state="readonly", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(pay_frame, text="Notes:").pack(side=tk.LEFT, padx=(20, 5))
        self.notes_entry = ttk.Entry(pay_frame, width=30)
        self.notes_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(checkout_frame, text="Generate Invoice", command=self.generate_invoice).pack(pady=10)

    def load_product_list(self):
        for row in self.prod_tree.get_children():
            self.prod_tree.delete(row)
        search = self.search_entry.get()
        products = self.db.search_products(search)
        for p in products:
            self.prod_tree.insert("", tk.END, values=(
                p["id"], p["name"],
                f"₹{p['sale_price']:.2f}" if p["sale_price"] else "₹0.00"
            ))

    def load_customers(self):
        customers = self.db.search_customers()
        vals = [f"{c['id']} - {c['name']} ({c['phone'] or 'No Phone'})" for c in customers]
        self.customer_combo["values"] = vals

    def add_to_cart(self):
        sel = self.prod_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a product first")
            return
        item = self.prod_tree.item(sel[0])
        prod_id = item["values"][0]
        prod_name = item["values"][1]
        price_str = item["values"][2].replace("₹", "")
        try:
            price = float(price_str)
        except:
            price = 0

        qty_dialog = tk.Toplevel(self.frame)
        qty_dialog.title("Enter Quantity")
        qty_dialog.geometry("300x280")
        qty_dialog.transient(self.frame)
        qty_dialog.grab_set()

        ttk.Label(qty_dialog, text=f"Product: {prod_name}", font=("Arial", 10, "bold")).pack(pady=10)
        ttk.Label(qty_dialog, text=f"Price: ₹{price:.2f}").pack()

        ttk.Label(qty_dialog, text="Quantity:").pack(pady=5)
        qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(qty_dialog, textvariable=qty_var, width=10)
        qty_entry.pack()
        qty_entry.select_range(0, tk.END)
        qty_entry.focus()

        ttk.Label(qty_dialog, text="Discount %:").pack(pady=5)
        disc_var = tk.StringVar(value="0")
        ttk.Entry(qty_dialog, textvariable=disc_var, width=10).pack()

        def confirm():
            try:
                qty = float(qty_var.get())
                disc = float(disc_var.get())
                if qty <= 0:
                    messagebox.showerror("Error", "Quantity must be > 0")
                    return
                total = qty * price * (1 - disc / 100)
                self.cart.append({
                    "product_id": prod_id,
                    "product_name": prod_name,
                    "quantity": qty,
                    "unit_price": price,
                    "discount_percent": disc,
                    "line_total": total
                })
                self.refresh_cart()
                qty_dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity or discount")

        ttk.Button(qty_dialog, text="Add", command=confirm).pack(pady=10)

    def on_drag_start(self, event):
        item = self.prod_tree.identify_row(event.y)
        if item:
            self.drag_item = item
            self.prod_tree.config(cursor="hand2")
        else:
            self.drag_item = None

    def on_drag_motion(self, event):
        pass

    def on_drag_release(self, event):
        if hasattr(self, 'drag_item') and self.drag_item:
            self.prod_tree.config(cursor="")
            try:
                widget = self.prod_tree.winfo_containing(event.x_root, event.y_root)
                # Check if it was dropped on the cart tree
                if widget == self.cart_tree:
                    self.prod_tree.selection_set(self.drag_item)
                    self.add_to_cart()
            except Exception:
                pass
            self.drag_item = None

    def refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        for item in self.cart:
            self.cart_tree.insert("", tk.END, values=(
                item["product_name"], item["quantity"],
                f"₹{item['unit_price']:.2f}", f"{item['discount_percent']:.0f}%",
                f"₹{item['line_total']:.2f}"
            ))
        self.calculate_totals()

    def calculate_totals(self):
        subtotal = sum(item["line_total"] for item in self.cart)
        total_items = sum(item["quantity"] for item in self.cart)
        if hasattr(self, 'total_items_label'):
            self.total_items_label.config(text=f"Total Items: {total_items:.0f}" if total_items.is_integer() else f"Total Items: {total_items:.2f}")
        
        disc_val = 0
        try:
            val = self.cart_discount_var.get()
            if val:
                disc_val = float(val)
        except ValueError:
            pass
        
        discount_amount = subtotal * (disc_val / 100.0)
        final_total = subtotal - discount_amount
        if final_total < 0:
            final_total = 0
            
        if hasattr(self, 'subtotal_label'):
            self.subtotal_label.config(text=f"₹{subtotal:.2f}")
        if hasattr(self, 'total_label'):
            self.total_label.config(text=f"₹{final_total:.2f}")

    def remove_from_cart(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = self.cart_tree.index(sel[0])
        if 0 <= idx < len(self.cart):
            del self.cart[idx]
            self.refresh_cart()

    def clear_cart(self):
        self.cart = []
        self.cart_discount_var.set("0")
        self.refresh_cart()

    def new_customer_dialog(self):
        dialog = tk.Toplevel(self.frame)
        dialog.title("New Customer")
        dialog.geometry("400x300")
        dialog.transient(self.frame)
        dialog.grab_set()

        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Phone:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        phone_entry = ttk.Entry(dialog, width=30)
        phone_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Email:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        email_entry = ttk.Entry(dialog, width=30)
        email_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Address:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        addr_entry = ttk.Entry(dialog, width=30)
        addr_entry.grid(row=3, column=1, padx=10, pady=5)

        def save():
            name = name_entry.get()
            if not name:
                messagebox.showerror("Error", "Name is required")
                return
            self.db.add_customer(name, phone_entry.get(), email_entry.get(), addr_entry.get())
            self.load_customers()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=4, column=0, columnspan=2, pady=20)

    def generate_invoice(self):
        if not self.cart:
            messagebox.showwarning("Warning", "Cart is empty")
            return

        customer_id = None
        cust_text = self.customer_combo.get()
        if cust_text and "-" in cust_text:
            try:
                customer_id = int(cust_text.split("-")[0].strip())
            except:
                pass

        subtotal = sum(item["line_total"] for item in self.cart)
        
        disc_val = 0
        try:
            val = self.cart_discount_var.get()
            if val:
                disc_val = float(val)
        except ValueError:
            pass
            
        discount_total = subtotal * (disc_val / 100.0)
        grand_total = subtotal - discount_total
        if grand_total < 0:
            grand_total = 0

        try:
            inv_no = self.db.create_invoice(
                customer_id, self.cart, subtotal, discount_total, grand_total,
                self.payment_var.get(), self.notes_entry.get()
            )
            self.auto_save_invoice_pdf(inv_no)
            messagebox.showinfo("Invoice Created", f"Invoice #{inv_no} generated successfully!")
            self.show_invoice_receipt(inv_no)
            self.cart = []
            self.cart_discount_var.set("0")
            self.refresh_cart()
            self.load_product_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create invoice: {e}")

    def show_invoice_receipt(self, inv_no):
        from utils.invoice_helper import show_invoice_receipt
        show_invoice_receipt(self.frame, self.db, inv_no)

    def auto_save_invoice_pdf(self, inv_no):
        try:
            invoice = self.db.conn.execute("SELECT * FROM invoices WHERE invoice_no=?", (inv_no,)).fetchone()
            if not invoice:
                return
            items = self.db.conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (invoice["id"],)).fetchall()
            
            customer = None
            if invoice["customer_id"]:
                customer = self.db.conn.execute("SELECT * FROM customers WHERE id=?", (invoice["customer_id"],)).fetchone()
            
            pdf_dir = os.path.join(os.getcwd(), "invoices")
            os.makedirs(pdf_dir, exist_ok=True)
            filename = os.path.join(pdf_dir, f"Invoice_{inv_no}.pdf")
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font('helvetica', 'B', 16)
            pdf.cell(0, 10, 'AD_CODER - INVOICE RECEIPT', border=False, ln=True, align='C')
            pdf.set_font('helvetica', 'I', 10)
            pdf.cell(0, 5, 'Firecracker Inventory Management System', border=False, ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(95, 6, f"Invoice No: {inv_no}", ln=False)
            pdf.cell(95, 6, f"Date: {invoice['invoice_date'][:19]}", ln=True, align="R")
            
            pdf.set_font("helvetica", "", 10)
            if customer:
                pdf.cell(0, 6, f"Customer: {customer['name']}", ln=True)
                if customer['phone']:
                    pdf.cell(0, 6, f"Phone: {customer['phone']}", ln=True)
                if customer['address']:
                    pdf.cell(0, 6, f"Address: {customer['address']}", ln=True)
            else:
                pdf.cell(0, 6, "Customer: Walk-in Customer", ln=True)
            pdf.ln(5)
            
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(90, 8, "Item", border=1)
            pdf.cell(20, 8, "Qty", border=1, align="C")
            pdf.cell(30, 8, "Price", border=1, align="R")
            pdf.cell(20, 8, "Disc %", border=1, align="C")
            pdf.cell(30, 8, "Total", border=1, align="R", ln=True)
            
            pdf.set_font("helvetica", "", 10)
            for item in items:
                pdf.cell(90, 8, str(item["product_name"]), border=1)
                pdf.cell(20, 8, f"{item['quantity']:.0f}", border=1, align="C")
                pdf.cell(30, 8, f"Rs. {item['unit_price']:.2f}", border=1, align="R")
                pdf.cell(20, 8, f"{item['discount_percent']:.0f}%", border=1, align="C")
                pdf.cell(30, 8, f"Rs. {item['line_total']:.2f}", border=1, align="R", ln=True)
            
            pdf.ln(5)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(140, 6, "Subtotal:", align="R")
            pdf.cell(50, 6, f"Rs. {invoice['subtotal']:.2f}", align="R", ln=True)
            if invoice["discount_total"]:
                pdf.cell(140, 6, "Discount:", align="R")
                pdf.cell(50, 6, f"-Rs. {invoice['discount_total']:.2f}", align="R", ln=True)
            pdf.cell(140, 6, "Grand Total:", align="R")
            pdf.cell(50, 6, f"Rs. {invoice['grand_total']:.2f}", align="R", ln=True)
            
            pdf.ln(5)
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 6, f"Payment Mode: {invoice['payment_mode']}", ln=True)
            if invoice["notes"]:
                pdf.cell(0, 6, f"Notes: {invoice['notes']}", ln=True)
            
            pdf.ln(10)
            pdf.set_font("helvetica", "I", 10)
            pdf.cell(0, 10, "Thank you! Visit Again!", align="C", ln=True)
            
            pdf.output(filename)
        except Exception as ex:
            print(f"Error auto-saving PDF: {ex}")
