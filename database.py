import sqlite3

def init_db():
    conn = sqlite3.connect('rentals.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sapboard_id TEXT,
            sapboard_name TEXT,
            admin_id INTEGER,
            admin_name TEXT,
            start_time TEXT,
            end_time TEXT,
            duration REAL,
            cost REAL
        )
    ''')
    conn.commit()
    conn.close()


def add_rental_start(user_id, sapboard_id, sapboard_name, admin_id, admin_name, start_time, end_time, duration, cost):
    conn = sqlite3.connect('rentals.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rentals (
            user_id, sapboard_id, sapboard_name, admin_id, admin_name, start_time, end_time, duration, cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, sapboard_id, sapboard_name, admin_id, admin_name, start_time, end_time, duration, cost))
    conn.commit()
    conn.close()


def get_all_rentals():
    conn = sqlite3.connect('rentals.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rentals ORDER BY start_time DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows
