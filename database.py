import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "jobs.db"
TABLE_NAME = "processed_jobs"

def get_connection():
    return sqlite3.connect(DB_NAME)

def generate_job_hash(org_name: str, role_name: str, job_url: str) -> str:
    """Deterministic hash based on org, role, and sanitized URL."""
    clean_url = job_url.split("?")[0].strip().lower()
    payload = f"{org_name.strip().lower()}|{role_name.strip().lower()}|{clean_url}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_hash TEXT UNIQUE,
                job_url TEXT,
                org_name TEXT,
                role_name TEXT,
                discovered_date TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def is_job_seen(org_name: str, role_name: str, job_url: str) -> bool:
    init_db()
    job_hash = generate_job_hash(org_name, role_name, job_url)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM {TABLE_NAME} WHERE job_hash = ?", (job_hash,))
        return cursor.fetchone() is not None

def mark_job_seen(org_name: str, role_name: str, job_url: str, post_date: str = None):
    init_db()
    job_hash = generate_job_hash(org_name, role_name, job_url)
    current_date = post_date or datetime.now().strftime("%d/%m/%Y")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT OR IGNORE INTO {TABLE_NAME} (job_hash, job_url, org_name, role_name, discovered_date)
            VALUES (?, ?, ?, ?, ?)
        """, (job_hash, job_url.strip(), org_name.strip(), role_name.strip(), current_date))
        conn.commit()