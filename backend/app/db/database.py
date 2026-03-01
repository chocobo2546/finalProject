# app/db/database.py
import sqlite3
import os
from contextlib import closing
from datetime import datetime

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

class Database:
    def __init__(self, db_path="app/data/data.db"):
        ensure_dir(db_path)
        self.db_path = db_path
        self._init_pragmas()

    def _conn(self):
        # create new connection per call (safe for threaded use)
        return sqlite3.connect(self.db_path, timeout=30)

    def _init_pragmas(self):
        # speed-friendly pragmas for WAL mode
        with closing(self._conn()) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA temp_store=MEMORY;")
            conn.execute("PRAGMA mmap_size=134217728;")  # 128MB
            conn.commit()

    def init_db(self):
        with closing(self._conn()) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price integer,
                gear TEXT,
                mile integer,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

    def save_item(self, item: dict):
        # Note: schema เป็น TEXT สำหรับ price/mile ก็จริง แต่เราบันทึกเป็น str/int ได้
        # (SQLite เก็บแบบ dynamic typing)
        with closing(self._conn()) as conn:
            conn.execute("""
            INSERT INTO cars (title, price, gear, mile, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item.get("title"),
                "" if item.get("price") is None else str(item.get("price")),
                item.get("gear"),
                "" if item.get("mile") is None else str(item.get("mile")),
                item.get("url"),
                datetime.utcnow()
            ))
            conn.commit()

    def get_all(self):
        # คืนข้อมูลดิบจาก DB ให้ service ไป normalize/validate ต่อ
        with closing(self._conn()) as conn:
            cur = conn.execute("""
                SELECT title, price, gear, mile, url, created_at
                FROM cars
                ORDER BY id ASC
            """)
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append({
                    "title": r[0],
                    "price": r[1],
                    "gear": r[2],
                    "mile": r[3],
                    "url": r[4],
                    "created_at": r[5],
                })
            return result

    def clear(self):
        with closing(self._conn()) as conn:
            conn.execute("DELETE FROM cars")
            conn.commit()
