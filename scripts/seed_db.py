"""
One-time synchronous script to seed ./data/catalog.db with realistic sample
data for the bonus database_query tool.

Run with:
    python scripts/seed_db.py

Two tables are created and populated:
  - products (15 rows)
  - orders   (20 rows, each referencing a product)
"""

import os
import sqlite3

DB_PATH = "./data/catalog.db"

PRODUCTS = [
    (1,  "Wireless Noise-Cancelling Headphones", "Electronics",   149.99, 120, "2025-01-05"),
    (2,  "Mechanical Keyboard",                  "Electronics",    89.99,  75,  "2025-01-08"),
    (3,  "USB-C Hub 7-in-1",                     "Electronics",    39.99,  200, "2025-01-10"),
    (4,  "Ergonomic Office Chair",               "Furniture",      299.99, 30,  "2025-01-15"),
    (5,  "Standing Desk Converter",              "Furniture",      179.99, 18,  "2025-01-20"),
    (6,  "Stainless Steel Water Bottle",         "Kitchen",        24.99,  350, "2025-02-01"),
    (7,  "Cold Brew Coffee Maker",               "Kitchen",        49.99,  90,  "2025-02-03"),
    (8,  "Yoga Mat Non-Slip",                    "Sports",         35.99,  160, "2025-02-10"),
    (9,  "Resistance Bands Set",                 "Sports",         19.99,  220, "2025-02-14"),
    (10, "Running Shoes",                        "Sports",         119.99, 55,  "2025-02-20"),
    (11, "Notebook Hardcover A5",                "Stationery",      9.99,  500, "2025-03-01"),
    (12, "Ballpoint Pen Set 12-pack",            "Stationery",      7.49,  800, "2025-03-02"),
    (13, "Desk Lamp LED Adjustable",             "Electronics",    44.99,  110, "2025-03-10"),
    (14, "Portable Bluetooth Speaker",           "Electronics",    59.99,  85,  "2025-03-15"),
    (15, "Bamboo Cutting Board",                 "Kitchen",        22.99,  140, "2025-03-20"),
]

ORDERS = [
    (1,  1,  "Alice Martin",    1, 149.99, "delivered", "2025-02-01"),
    (2,  3,  "Bob Chen",        2,  79.98, "delivered", "2025-02-03"),
    (3,  8,  "Carol White",     1,  35.99, "delivered", "2025-02-10"),
    (4,  6,  "David Kim",       3,  74.97, "shipped",   "2025-02-15"),
    (5,  2,  "Eve Patel",       1,  89.99, "delivered", "2025-02-18"),
    (6,  10, "Frank Lopez",     1, 119.99, "delivered", "2025-02-22"),
    (7,  4,  "Grace Müller",    1, 299.99, "delivered", "2025-02-25"),
    (8,  7,  "Hank Nguyen",     1,  49.99, "shipped",   "2025-03-01"),
    (9,  9,  "Iris Brown",      2,  39.98, "delivered", "2025-03-04"),
    (10, 13, "Jack Turner",     1,  44.99, "delivered", "2025-03-12"),
    (11, 14, "Karen Scott",     1,  59.99, "shipped",   "2025-03-16"),
    (12, 11, "Liam Hall",       5,  49.95, "delivered", "2025-03-18"),
    (13, 5,  "Mia Adams",       1, 179.99, "pending",   "2025-03-22"),
    (14, 12, "Noah Clark",      3,  22.47, "delivered", "2025-03-25"),
    (15, 15, "Olivia Lewis",    2,  45.98, "shipped",   "2025-03-28"),
    (16, 1,  "Paul Robinson",   1, 149.99, "pending",   "2025-04-01"),
    (17, 3,  "Quinn Walker",    4, 159.96, "pending",   "2025-04-02"),
    (18, 8,  "Rachel Young",    2,  71.98, "shipped",   "2025-04-03"),
    (19, 6,  "Sam Harris",      1,  24.99, "delivered", "2025-04-04"),
    (20, 2,  "Tina Martinez",   1,  89.99, "pending",   "2025-04-05"),
]


def seed() -> None:
    """
    Create ./data/catalog.db, create the products and orders tables, and
    insert sample rows. Existing tables are dropped and recreated so the
    script is safely re-runnable.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;

        CREATE TABLE products (
            id             INTEGER PRIMARY KEY,
            name           TEXT    NOT NULL,
            category       TEXT    NOT NULL,
            price          REAL    NOT NULL,
            stock_quantity INTEGER NOT NULL,
            created_at     TEXT    NOT NULL
        );

        CREATE TABLE orders (
            id            INTEGER PRIMARY KEY,
            product_id    INTEGER NOT NULL REFERENCES products(id),
            customer_name TEXT    NOT NULL,
            quantity      INTEGER NOT NULL,
            total_price   REAL    NOT NULL,
            status        TEXT    NOT NULL,
            created_at    TEXT    NOT NULL
        );
    """)

    cur.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)",
        PRODUCTS,
    )

    cur.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
        ORDERS,
    )

    con.commit()
    con.close()

    print(f"Seeded {len(PRODUCTS)} products and {len(ORDERS)} orders into {DB_PATH}")


if __name__ == "__main__":
    seed()
