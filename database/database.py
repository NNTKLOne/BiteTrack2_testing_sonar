import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "database", "data.db")

class Database:

    def __init__(self):
        self.db_file = DB_FILE
        self.create_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def add_product(self, product_name, created_at=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        if created_at is None:
            cursor.execute('INSERT INTO Product (product_name) VALUES (?)', (product_name,))
        else:
            cursor.execute('INSERT INTO Product (product_name, created_at) VALUES (?, ?)',
                           (product_name, created_at))

        conn.commit()
        conn.close()

    def update_product(self, product_id, product_name):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE Product SET product_name = ? WHERE id = ?', (product_name, product_id))
        conn.commit()
        conn.close()

    def get_all_products(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Product ORDER BY created_at DESC')
        products = cursor.fetchall()
        conn.close()
        return [dict(p) for p in products]

    def delete_all_products(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Product')
        conn.commit()
        conn.close()

    def delete_product(self, product_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Product WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()

    def get_products_today(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM Product 
            WHERE DATE(created_at) = DATE('now') 
            ORDER BY created_at DESC
        """)
        products = cursor.fetchall()
        conn.close()
        return [dict(p) for p in products]

    def get_products_this_week(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM Product
            WHERE strftime('%W', created_at) = strftime('%W', 'now')
            AND strftime('%Y', created_at) = strftime('%Y', 'now')
            ORDER BY created_at DESC
        """)
        products = cursor.fetchall()
        conn.close()
        return [dict(p) for p in products]

    def get_products_this_month(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM Product
            WHERE strftime('%m', created_at) = strftime('%m', 'now')
            AND strftime('%Y', created_at) = strftime('%Y', 'now')
            ORDER BY created_at DESC
        """)
        products = cursor.fetchall()
        conn.close()
        return [dict(p) for p in products]

