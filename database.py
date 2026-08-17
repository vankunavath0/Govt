import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "jobs.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def generate_job_hash(org_name: str, role_name: str, job_url: str) -> str:
    """Creates a unique deterministic fingerprint for each job listing."""
    normalized_str = f"{org_name.strip().lower()}|{role_name.strip().lower()}|{job_url.split('?')[0].strip()}"
    return hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seen_jobs'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(seen_jobs)")
            cols = [col[1] for col in cursor.fetchall()]
            # If missing job_hash column, drop the outdated table
            if "job_hash" not in cols:
                cursor.execute("DROP TABLE seen_jobs")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
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
        cursor.execute("SELECT 1 FROM seen_jobs WHERE job_hash = ?", (job_hash,))
        return cursor.fetchone() is not None

def mark_job_seen(org_name: str, role_name: str, job_url: str, post_date: str = None):
    init_db()
    job_hash = generate_job_hash(org_name, role_name, job_url)
    current_date = post_date or datetime.now().strftime("%d/%m/%Y")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO seen_jobs (job_hash, job_url, org_name, role_name, discovered_date)
            VALUES (?, ?, ?, ?, ?)
        """, (job_hash, job_url.strip(), org_name.strip(), role_name.strip(), current_date))
        conn.commit()