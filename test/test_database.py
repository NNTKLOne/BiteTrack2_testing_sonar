import os
import unittest
import sqlite3
from datetime import datetime, timedelta

from database.database import Database
from pathlib import Path

TEST_DB = Path(__file__).parent / 'test_data.db'

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = Database()
        self.db.db_file = TEST_DB
        self.db.create_tables()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_create_tables(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Product'")
        table = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table)

    def test_add_product(self):
        self.db.add_product("Apple")
        products = self.db.get_all_products()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['product_name'], 'Apple')

    def test_get_all_products_empty(self):
        products = self.db.get_all_products()
        self.assertEqual(len(products), 0)

    def test_add_multiple_products(self):
        self.db.add_product("Apple")
        self.db.add_product("Banana")
        products = self.db.get_all_products()
        self.assertEqual(len(products), 2)
        self.assertEqual(products[1]['product_name'], 'Banana')

    def test_delete_product(self):
        self.db.add_product("Apple")
        products = self.db.get_all_products()
        self.assertEqual(len(products), 1)

        product_id = products[0]['id']
        self.db.delete_product(product_id)

        products = self.db.get_all_products()
        self.assertEqual(len(products), 0)

    def test_get_products_today(self):
        self.db.add_product("Apple")
        products = self.db.get_products_today()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['product_name'], "Apple")

    def test_get_products_this_week(self):
        self.db.add_product("Apple")
        products = self.db.get_products_this_week()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['product_name'], "Apple")

        past_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO Product (product_name, created_at) VALUES (?, ?)',
            ("Old Apple", past_date)
        )
        conn.commit()
        conn.close()

        products = self.db.get_products_this_week()
        self.assertEqual(len(products), 1)  # Senas produktas neturėtų būti rodomas

    def test_get_products_this_month(self):
        self.db.add_product("Apple")
        products = self.db.get_products_this_month()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['product_name'], "Apple")

        past_date = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d %H:%M:%S')
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO Product (product_name, created_at) VALUES (?, ?)',
            ("Old Apple", past_date)
        )
        conn.commit()
        conn.close()

        products = self.db.get_products_this_month()
        self.assertEqual(len(products), 1)

    def test_get_products_today_empty(self):
        products = self.db.get_products_today()
        self.assertEqual(len(products), 0)

    def test_get_products_this_week_empty(self):
        products = self.db.get_products_this_week()
        self.assertEqual(len(products), 0)

    def test_get_products_this_month_empty(self):
        products = self.db.get_products_this_month()
        self.assertEqual(len(products), 0)

if __name__ == '__main__':
    unittest.main()
