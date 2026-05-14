import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).parent / "planner.db"

DEFAULT_ROUTINE = [
    "기상", "헬스장", "아침식사", "아일라", "대중교통", "출근",
    "오픈완료", "점심식사", "알바출근", "퇴근", "저녁식사", "취침"
]

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            date TEXT NOT NULL,
            item TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (date, item)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS routine_items (
            position INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    """)
    return conn

def init_routine_if_empty():
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM routine_items")
    if cur.fetchone()[0] == 0:
        for i, name in enumerate(DEFAULT_ROUTINE):
            conn.execute(
                "INSERT INTO routine_items (position, name) VALUES (?, ?)",
                (i, name)
            )
        conn.commit()
    conn.close()

def get_routine() -> list:
    conn = get_conn()
    cur = conn.execute("SELECT name FROM routine_items ORDER BY position")
    result = [row[0] for row in cur.fetchall()]
    conn.close()
    return result

def add_routine_item(name: str) -> bool:
    conn = get_conn()
    try:
        cur = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM routine_items")
        next_pos = cur.fetchone()[0]
        conn.execute(
            "INSERT INTO routine_items (position, name) VALUES (?, ?)",
            (next_pos, name)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_routine_item(name: str):
    conn = get_conn()
    conn.execute("DELETE FROM routine_items WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def move_routine_item(name: str, direction: int):
    conn = get_conn()
    cur = conn.execute("SELECT position FROM routine_items WHERE name = ?", (name,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return
    cur_pos = row[0]
    new_pos = cur_pos + direction
    
    cur = conn.execute("SELECT name FROM routine_items WHERE position = ?", (new_pos,))
    swap_row = cur.fetchone()
    if swap_row is None:
        conn.close()
        return
    swap_name = swap_row[0]
    
    conn.execute("UPDATE routine_items SET position = -1 WHERE name = ?", (name,))
    conn.execute("UPDATE routine_items SET position = ? WHERE name = ?", (cur_pos, swap_name))
    conn.execute("UPDATE routine_items SET position = ? WHERE name = ?", (new_pos, name))
    conn.commit()
    conn.close()

def load_day(d: date) -> dict:
    conn = get_conn()
    cur = conn.execute(
        "SELECT item, value FROM records WHERE date = ?",
        (d.isoformat(),)
    )
    result = dict(cur.fetchall())
    conn.close()
    return result

def load_range(start: date, end: date) -> dict:
    """start~end 사이의 모든 기록을 {(date, item): value} 형태로 반환"""
    conn = get_conn()
    cur = conn.execute(
        "SELECT date, item, value FROM records WHERE date BETWEEN ? AND ?",
        (start.isoformat(), end.isoformat())
    )
    result = {}
    for d_str, item, value in cur.fetchall():
        result[(d_str, item)] = value
    conn.close()
    return result

def save_record(d: date, item: str, value: str):
    conn = get_conn()
    conn.execute(
        """INSERT INTO records (date, item, value) VALUES (?, ?, ?)
           ON CONFLICT(date, item) DO UPDATE SET value = excluded.value""",
        (d.isoformat(), item, value)
    )
    conn.commit()
    conn.close()

def delete_record(d: date, item: str):
    conn = get_conn()
    conn.execute(
        "DELETE FROM records WHERE date = ? AND item = ?",
        (d.isoformat(), item)
    )
    conn.commit()
    conn.close()

def load_all() -> list:
    conn = get_conn()
    cur = conn.execute("SELECT date, item, value FROM records ORDER BY date, item")
    result = cur.fetchall()
    conn.close()
    return result