def center_window(window, parent):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    
    root = parent.winfo_toplevel()
    p_width = root.winfo_width()
    p_height = root.winfo_height()
    p_x = root.winfo_x()
    p_y = root.winfo_y()
    
    x = p_x + (p_width // 2) - (width // 2)
    y = p_y + (p_height // 2) - (height // 2)
    window.geometry(f"+{x}+{y}")
