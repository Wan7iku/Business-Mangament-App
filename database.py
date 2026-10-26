import sqlite3

DATABASE = "business.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            payment_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            amount REAL NOT NULL CHECK (amount > 0),
            payment_method TEXT NOT NULL,
            reference TEXT,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id)
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL CHECK (amount > 0),
            payment_method TEXT NOT NULL,
            reference TEXT
        )
    """)

    conn.commit()
    conn.close()

