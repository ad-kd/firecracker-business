import os
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from fpdf import FPDF

def show_invoice_receipt(parent_frame, db, inv_no):
    invoice = db.conn.execute("SELECT * FROM invoices WHERE invoice_no=?", (inv_no,)).fetchone()
    if not invoice:
        return
    items = db.conn.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (invoice["id"],)).fetchall()

    from utils.gui_helper import center_window
    dialog = tk.Toplevel(parent_frame)
    dialog.title(f"Invoice {inv_no}")
    dialog.geometry("500x550")
    center_window(dialog, parent_frame)
    dialog.transient(parent_frame)
    dialog.grab_set()

    text = tk.Text(dialog, font=("Courier", 10))
    text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    lines = []
    lines.append("=" * 50)
    lines.append("                     AD_CODER")
    lines.append("         Firecracker Inventory")
    lines.append("=" * 50)
    lines.append(f"Invoice: {inv_no}")
    lines.append(f"Date: {invoice['invoice_date'][:19]}")
    lines.append("-" * 50)
    lines.append(f"{'Item':<25} {'Qty':>5} {'Price':>8} {'Total':>8}")
    lines.append("-" * 50)
    for item in items:
        name = item["product_name"][:24]
        qty = f"{item['quantity']:.0f}"
        price = f"{item['unit_price']:.2f}"
        total = f"{item['line_total']:.2f}"
        lines.append(f"{name:<25} {qty:>5} {price:>8} {total:>8}")
    lines.append("-" * 50)
    lines.append(f"{'Subtotal:':>40} ₹{invoice['subtotal']:.2f}")
    if invoice["discount_total"]:
        lines.append(f"{'Discount:':>40} -₹{invoice['discount_total']:.2f}")
    lines.append(f"{'Grand Total:':>40} ₹{invoice['grand_total']:.2f}")
    lines.append("=" * 50)
    lines.append(f"Payment: {invoice['payment_mode']}")
    if invoice["notes"]:
        lines.append(f"Notes: {invoice['notes']}")
    lines.append("=" * 50)
    lines.append("        Thank you! Visit Again!")

    text.insert(tk.END, "\n".join(lines))
    text.config(state=tk.DISABLED)

    # Action Buttons
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=10)

    def save_pdf():
        filename = filedialog.asksaveasfilename(
            title="Save Invoice PDF",
            initialfile=f"Invoice_{inv_no}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not filename:
            return
        try:
            customer = None
            if invoice["customer_id"]:
                customer = db.conn.execute("SELECT * FROM customers WHERE id=?", (invoice["customer_id"],)).fetchone()
            
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
            messagebox.showinfo("Success", f"Invoice saved to {filename}")
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save PDF: {ex}")

    def print_receipt():
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"print_{inv_no}.txt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(text.get("1.0", tk.END))
            os.startfile(temp_file, "print")
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to print: {ex}\nYou can still save the invoice as a PDF and print it from your PDF viewer.")

    ttk.Button(btn_frame, text="Save as PDF", command=save_pdf).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    ttk.Button(btn_frame, text="Print Receipt", command=print_receipt).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)
