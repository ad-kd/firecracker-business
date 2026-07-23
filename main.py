import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from database.db_manager import DatabaseManager
from views.main_window import MainWindow


def main():
    db = DatabaseManager()
    root = tk.Tk()
    app = MainWindow(root, db)
    root.mainloop()
    db.close()


if __name__ == "__main__":
    main()
