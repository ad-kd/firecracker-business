import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ad_coder.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.seed_products()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT NOT NULL,
                category_id INTEGER,
                unit TEXT DEFAULT 'PCS',
                sale_price REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                quantity_on_hand REAL DEFAULT 0,
                reorder_level REAL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT NOT NULL UNIQUE,
                customer_id INTEGER,
                invoice_date TEXT DEFAULT (datetime('now')),
                subtotal REAL DEFAULT 0,
                discount_total REAL DEFAULT 0,
                grand_total REAL DEFAULT 0,
                payment_mode TEXT DEFAULT 'CASH',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT,
                quantity REAL DEFAULT 1,
                unit_price REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_no TEXT NOT NULL UNIQUE,
                supplier_name TEXT,
                purchase_date TEXT DEFAULT (datetime('now')),
                total_amount REAL DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT,
                quantity REAL DEFAULT 0,
                unit_price REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                description TEXT,
                amount REAL DEFAULT 0,
                expense_date TEXT DEFAULT (datetime('now')),
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        # Drop gstin column if it exists and version supports it
        try:
            cursor.execute("PRAGMA table_info(customers)")
            columns = [row[1] for row in cursor.fetchall()]
            if "gstin" in columns:
                cursor.execute("ALTER TABLE customers DROP COLUMN gstin")
        except Exception:
            pass
        self.conn.commit()

    def seed_products(self):
        count = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count > 0:
            return

        categories = [
            ("LAKSHMI CRACKERS", "Lakshmi brand crackers"),
            ("SOUND CRACKERS", "Paper sound bombs and crackers"),
            ("BULLET CRACKERS", "Bullet crackers various counts"),
            ("MEGA BULLET", "Mega bullet crackers"),
            ("BIJILLI CRACKERS", "Bijilli crackers"),
            ("FLOWERPOTS", "Flowerpot varieties"),
            ("GROUND CHAKKAR", "Ground chakkar varieties"),
            ("AUTO BOMB", "Auto bomb varieties"),
            ("TWINKLING STAR", "Twinkling star varieties"),
            ("PENCIL", "Pencil crackers"),
            ("ROCKETS", "Rocket varieties"),
            ("FANCY NOVELTY", "Fancy novelty items"),
            ("SPARKLERS", "Sparkler varieties"),
            ("AERIAL SHOT", "Aerial shot varieties"),
            ("MULTISHOT", "Multishot functions"),
            ("DAY SHOT", "Day shot crackers"),
            ("CAP CRACKERS", "Cap crackers and matches"),
            ("SERPENT EGG", "Serpent egg varieties"),
        ]
        for name, desc in categories:
            self.conn.execute("INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)", (name, desc))
        self.conn.commit()

        cat_map = {}
        for row in self.conn.execute("SELECT id, name FROM categories").fetchall():
            cat_map[row["name"]] = row["id"]

        products = [
            (1, "3 LAKSHMI", "LAKSHMI CRACKERS"),
            (2, '4" LAKSHMI', "LAKSHMI CRACKERS"),
            (3, '4" LAKSHMI / KRISHNA 8 PLY', "LAKSHMI CRACKERS"),
            (4, '4 MEGALAKSHMI 12 PLY', "LAKSHMI CRACKERS"),
            (5, '4" GOLD LAKSHMI', "LAKSHMI CRACKERS"),
            (6, '4" LAKSHMI / PARROT 16 PLY', "LAKSHMI CRACKERS"),
            (7, "2 KURUVI", "LAKSHMI CRACKERS"),
            (8, "PAPER SOUND BOMB", "SOUND CRACKERS"),
            (9, "PAPER SOUND BOMB COLOR", "SOUND CRACKERS"),
            (10, "MAGIC SHOW (MONEY)", "SOUND CRACKERS"),
            (11, "PAPER SOUND BOMB 1/2 KG", "SOUND CRACKERS"),
            (12, "PAPER SOUND BOMB 3/4 KG", "SOUND CRACKERS"),
            (13, "PAPER SOUND BOMB 1 KG", "SOUND CRACKERS"),
            (14, "28 MINI BULLET", "BULLET CRACKERS"),
            (15, "56 MINI BULLET", "BULLET CRACKERS"),
            (16, "28 MEDIUM BULLET", "BULLET CRACKERS"),
            (17, "56 MEDIUM BULLET", "BULLET CRACKERS"),
            (18, "24 MEGA BULLET", "MEGA BULLET"),
            (19, "28 MEGA BULLET", "MEGA BULLET"),
            (20, "50 MEGA BULLET", "MEGA BULLET"),
            (21, "100 MEGA BULLET", "MEGA BULLET"),
            (22, "100", "MEGA BULLET"),
            (23, "200", "MEGA BULLET"),
            (24, "1K", "MEGA BULLET"),
            (25, "2K", "MEGA BULLET"),
            (26, "5K", "MEGA BULLET"),
            (27, "10K", "MEGA BULLET"),
            (28, "1K SPECIAL", "MEGA BULLET"),
            (29, "2K SPECIAL", "MEGA BULLET"),
            (30, "5K SPECIAL", "MEGA BULLET"),
            (31, "10K SPECIAL", "MEGA BULLET"),
            (32, "RED BIJILLI", "BIJILLI CRACKERS"),
            (33, "STRIPPED BIJILLI", "BIJILLI CRACKERS"),
            (34, "FLOWERPOT SMALL", "FLOWERPOTS"),
            (35, "FLOWERPOT BIG", "FLOWERPOTS"),
            (36, "FLOWERPOT SPECIAL", "FLOWERPOTS"),
            (37, "FLOWERPOT ASHOKA", "FLOWERPOTS"),
            (38, "COLOR KOTI", "FLOWERPOTS"),
            (39, "COLOR KOTI DELUXE", "FLOWERPOTS"),
            (40, "FLOWERPOT DELUXE 5'S", "FLOWERPOTS"),
            (41, "GROUND CHAKKAR BIG 10'S", "GROUND CHAKKAR"),
            (42, "GROUND CHAKKAR BIG 25'S", "GROUND CHAKKAR"),
            (43, "GROUND CHAKKAR ASHOKA", "GROUND CHAKKAR"),
            (44, "GROUND CHAKKAR SPECIAL", "GROUND CHAKKAR"),
            (45, "GROUND CHAKKAR DELUXE", "GROUND CHAKKAR"),
            (46, "HYDRO BOMB", "AUTO BOMB"),
            (47, "KING OF KING GREEN", "AUTO BOMB"),
            (48, "CLASSIC BOMB GREEN", "AUTO BOMB"),
            (49, "777 AGNI", "AUTO BOMB"),
            (50, "DIGITAL BOMB 12PLY", "AUTO BOMB"),
            (51, "1 1/2 TWINKLING STAR", "TWINKLING STAR"),
            (52, "4 TWINKLING STAR", "TWINKLING STAR"),
            (53, "CANDLE PEN", "PENCIL"),
            (54, "WATER FALLS PENCIL", "PENCIL"),
            (55, "12 PENCIL", "PENCIL"),
            (56, "BABY ROCKET", "ROCKETS"),
            (57, "ROCKET BOMB", "ROCKETS"),
            (58, "COLOR ROCKET", "ROCKETS"),
            (59, "LUNIK ROCKET", "ROCKETS"),
            (60, "TWO SOUND ROCKET", "ROCKETS"),
            (61, "WHISTLING ROCKET", "ROCKETS"),
            (62, "GANGA JAMUNA", "FANCY NOVELTY"),
            (63, "MINI SIREN (5 PCS)", "FANCY NOVELTY"),
            (64, "KING SIREN (3 PCS)", "FANCY NOVELTY"),
            (65, "KITKAT SMALL", "FANCY NOVELTY"),
            (66, "KITKAT BIG", "FANCY NOVELTY"),
            (67, "BUTTERFLY WINGS FIGHTER", "FANCY NOVELTY"),
            (68, "BAMBARAM", "FANCY NOVELTY"),
            (69, '2" FOUNTAIN', "FANCY NOVELTY"),
            (70, "TRICOLOR FOUNTAIN", "FANCY NOVELTY"),
            (71, "DORE SINGER", "FANCY NOVELTY"),
            (72, "DRAGON STAR", "FANCY NOVELTY"),
            (73, "TIN BEER", "FANCY NOVELTY"),
            (74, "TIN BEER (YAZHI)", "FANCY NOVELTY"),
            (75, "KING OF HITLER TIN", "FANCY NOVELTY"),
            (76, "MANSA MUSA TIN", "FANCY NOVELTY"),
            (77, "WATER QUEEN TIN", "FANCY NOVELTY"),
            (78, "PHOTO FLASH", "FANCY NOVELTY"),
            (79, "HELICOPTER", "FANCY NOVELTY"),
            (80, "TOP GUN", "FANCY NOVELTY"),
            (81, "PISTOL GUN", "FANCY NOVELTY"),
            (82, "PLANET WHEEL", "FANCY NOVELTY"),
            (83, "4*4 WHEEL", "FANCY NOVELTY"),
            (84, "LOLLIPOP STICK", "FANCY NOVELTY"),
            (85, "BAT BALL", "FANCY NOVELTY"),
            (86, "COLOR SMOKE", "FANCY NOVELTY"),
            (87, "PEACOCK SMALL", "FANCY NOVELTY"),
            (88, "PEACOCK BIG", "FANCY NOVELTY"),
            (89, "PEACOCK BADA", "FANCY NOVELTY"),
            (90, "WATTS", "FANCY NOVELTY"),
            (91, "SHINCHAN", "FANCY NOVELTY"),
            (92, "FIRE EGG", "FANCY NOVELTY"),
            (93, "WIRE CHAKKAR", "FANCY NOVELTY"),
            (94, "WATER FALLS", "FANCY NOVELTY"),
            (95, "MUSICAL ROCKET", "FANCY NOVELTY"),
            (96, "EMU EGG", "FANCY NOVELTY"),
            (97, "SUN LIGHT", "FANCY NOVELTY"),
            (98, "MAGIC SHOW", "FANCY NOVELTY"),
            (99, "APPU SHOWER", "FANCY NOVELTY"),
            (100, "CAR", "FANCY NOVELTY"),
            (101, '3" FANCY', "FANCY NOVELTY"),
            (102, "TOM JERRY", "FANCY NOVELTY"),
            (103, "WONDER (MIX)", "FANCY NOVELTY"),
            (104, "DINOSUR", "FANCY NOVELTY"),
            (105, "TORNADO", "FANCY NOVELTY"),
            (106, "CHAKKARAM CELEBRATION", "FANCY NOVELTY"),
            (107, "WOW", "FANCY NOVELTY"),
            (108, "FALLS", "FANCY NOVELTY"),
            (109, "SEA HOURSE", "FANCY NOVELTY"),
            (110, "HI COO", "FANCY NOVELTY"),
            (111, "SKY COLOR", "FANCY NOVELTY"),
            (112, "CHUKKI (MIX)", "FANCY NOVELTY"),
            (113, "SPARK", "FANCY NOVELTY"),
            (114, "LITTLE HEART", "FANCY NOVELTY"),
            (115, "CUTE SPARKLES", "FANCY NOVELTY"),
            (116, "7CM ELECTRIC SPARKLERS", "SPARKLERS"),
            (117, "7CM COLOR SPARKLERS", "SPARKLERS"),
            (118, "7CM GREEN SPARKLERS", "SPARKLERS"),
            (119, "7CM RED SPARKLERS", "SPARKLERS"),
            (120, "10CM ELECTRIC SPARKLERS", "SPARKLERS"),
            (121, "10CM COLOR SPARKLERS", "SPARKLERS"),
            (122, "10CM GREEN SPARKLERS", "SPARKLERS"),
            (123, "10CM RED SPARKLERS", "SPARKLERS"),
            (124, "12CM ELECTRIC SPARKLERS", "SPARKLERS"),
            (125, "12CM COLOR SPARKLERS", "SPARKLERS"),
            (126, "12CM GREEN SPARKLERS", "SPARKLERS"),
            (127, "12CM RED SPARKLERS", "SPARKLERS"),
            (128, "15CM ELECTRIC SPARKLERS", "SPARKLERS"),
            (129, "15CM COLOR SPARKLERS", "SPARKLERS"),
            (130, "15CM GREEN SPARKLERS", "SPARKLERS"),
            (131, "15CM RED SPARKLERS", "SPARKLERS"),
            (132, "30CM ELECTRIC SPARKLERS", "SPARKLERS"),
            (133, "30CM COLOR SPARKLERS", "SPARKLERS"),
            (134, "30CM GREEN SPARKLERS", "SPARKLERS"),
            (135, "30CM RED SPARKLERS", "SPARKLERS"),
            (136, "50CM ELECTRIC SPARKLERS (5 PCS)", "SPARKLERS"),
            (137, "50CM COLOR SPARKLERS (5 PCS)", "SPARKLERS"),
            (138, '1" CHOTTA FANCY', "AERIAL SHOT"),
            (139, '2" FANCY', "AERIAL SHOT"),
            (140, "3 PCS FANCY", "AERIAL SHOT"),
            (141, '3 1/2" FANCY SINGLE', "AERIAL SHOT"),
            (142, '3 1/2" NAYAGARA FALLS', "AERIAL SHOT"),
            (143, '3 1/2" DIGITAL STAR', "AERIAL SHOT"),
            (144, '3 1/2" FANCY DOUBLE (MOTHERS)', "AERIAL SHOT"),
            (145, '3 1/2" FANCY 7 STEP (MOTHERS)', "AERIAL SHOT"),
            (146, '4" FANCY', "AERIAL SHOT"),
            (147, '4" FANCY (2 PCS)', "AERIAL SHOT"),
            (148, '5" FANCY', "AERIAL SHOT"),
            (149, "12 SHOT CRACKLING", "MULTISHOT"),
            (150, "25 SHOT CRACKLING", "MULTISHOT"),
            (151, "30 SHOT CRACKLING", "MULTISHOT"),
            (152, "60 SHOT CRACKLING", "MULTISHOT"),
            (153, "12 SHOT WHISTLING", "MULTISHOT"),
            (154, "25 SHOT WHISTLING", "MULTISHOT"),
            (155, "7 SHOT MULTICOLOR", "MULTISHOT"),
            (156, "12 SHOT MULTICOLOR", "MULTISHOT"),
            (157, "30 SHOT MULTICOLOR (GURUJI)", "MULTISHOT"),
            (158, "60 SHOT MULTICOLOR", "MULTISHOT"),
            (159, "120 SHOT MULTICOLOR", "MULTISHOT"),
            (160, "240 SHOT MULTICOLOR", "MULTISHOT"),
            (161, '2" SETOUT', "DAY SHOT"),
            (162, '2 1/2" SETOUT', "DAY SHOT"),
            (163, '3" SETOUT', "DAY SHOT"),
            (164, "ROLL CAP COLOR MATCHES", "CAP CRACKERS"),
            (165, "RIDER COLOR MATCHES", "CAP CRACKERS"),
            (166, "LOLLIPOP MATCHES", "CAP CRACKERS"),
            (167, "ANACONDA BIG SIZE", "SERPENT EGG"),
        ]

        for code, name, cat_name in products:
            cat_id = cat_map.get(cat_name)
            self.conn.execute(
                "INSERT INTO products (code, name, category_id, unit, sale_price, discount_percent, quantity_on_hand) VALUES (?, ?, ?, 'PCS', 0, 0, 0)",
                (str(code), name, cat_id)
            )
        self.conn.commit()

    def get_categories(self):
        return self.conn.execute("SELECT * FROM categories ORDER BY name").fetchall()

    def search_products(self, search_term="", category_id=None):
        query = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1"
        params = []
        if search_term:
            query += " AND (p.name LIKE ? OR p.code LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        query += " ORDER BY p.code, p.name"
        return self.conn.execute(query, params).fetchall()

    def add_product(self, name, code, category_id, unit, sale_price, discount_percent):
        self.conn.execute(
            "INSERT INTO products (code, name, category_id, unit, sale_price, discount_percent, quantity_on_hand) VALUES (?, ?, ?, ?, ?, ?, 0)",
            (code, name, category_id, unit, sale_price, discount_percent)
        )
        self.conn.commit()
        return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def update_product(self, pid, name, code, category_id, unit, sale_price, discount_percent):
        self.conn.execute(
            "UPDATE products SET code=?, name=?, category_id=?, unit=?, sale_price=?, discount_percent=?, updated_at=datetime('now') WHERE id=?",
            (code, name, category_id, unit, sale_price, discount_percent, pid)
        )
        self.conn.commit()

    def delete_product(self, pid):
        self.conn.execute("DELETE FROM products WHERE id=?", (pid,))
        self.conn.commit()

    def add_customer(self, name, phone, email, address):
        self.conn.execute(
            "INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
            (name, phone, email, address)
        )
        self.conn.commit()
        return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def search_customers(self, search_term=""):
        query = "SELECT * FROM customers WHERE 1=1"
        params = []
        if search_term:
            query += " AND (name LIKE ? OR phone LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        query += " ORDER BY name"
        return self.conn.execute(query, params).fetchall()

    def update_customer(self, cid, name, phone, email, address):
        self.conn.execute(
            "UPDATE customers SET name=?, phone=?, email=?, address=? WHERE id=?",
            (name, phone, email, address, cid)
        )
        self.conn.commit()

    def delete_customer(self, cid):
        self.conn.execute("DELETE FROM customers WHERE id=?", (cid,))
        self.conn.commit()

    def create_invoice(self, customer_id, items, subtotal, discount_total, grand_total, payment_mode="CASH", notes=""):
        inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor = self.conn.execute(
            "INSERT INTO invoices (invoice_no, customer_id, subtotal, discount_total, grand_total, payment_mode, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (inv_no, customer_id, subtotal, discount_total, grand_total, payment_mode, notes)
        )
        invoice_id = cursor.lastrowid
        for item in items:
            self.conn.execute(
                "INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, unit_price, discount_percent, line_total) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (invoice_id, item["product_id"], item["product_name"], item["quantity"], item["unit_price"], item["discount_percent"], item["line_total"])
            )
        self.conn.commit()
        return inv_no

    def get_invoices(self, limit=100):
        return self.conn.execute("""
            SELECT i.*, c.name as customer_name
            FROM invoices i LEFT JOIN customers c ON i.customer_id = c.id
            ORDER BY i.created_at DESC LIMIT ?
        """, (limit,)).fetchall()

    def get_invoice_details(self, invoice_id):
        invoice = self.conn.execute("""
            SELECT i.*, c.name as customer_name, c.phone as customer_phone, c.address as customer_address
            FROM invoices i LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id = ?
        """, (invoice_id,)).fetchone()
        items = self.conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
        return invoice, items

    def get_dashboard_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        total_products = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_customers = self.conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        total_sales = self.conn.execute("SELECT COALESCE(SUM(grand_total), 0) FROM invoices WHERE date(created_at) = ?", (today,)).fetchone()[0]
        return {
            "total_products": total_products,
            "total_customers": total_customers,
            "today_sales": total_sales,
        }

    def close(self):
        self.conn.close()
