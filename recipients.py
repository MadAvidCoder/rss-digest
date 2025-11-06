## Handles reading recipients from the db

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List
import config

logger = logging.getLogger(__name__)

DB_URL = getattr(config, "DB_URL", None) or os.environ.get("DB_URL")

def _get_conn():
    if not DB_URL:
        raise RuntimeError("DB_URL not configured; cannot access recipients table")
    return psycopg2.connect(DB_URL)

def ensure_table():
    sql = """
    CREATE TABLE IF NOT EXISTS recipients (
    email TEXT PRIMARY KEY,
    added_at TIMESTAMPTZ DEFAULT now()
    );
    """
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()

def get_recipients() -> List[str]:
    ensure_table()
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT email FROM recipients ORDER BY added_at DESC;")
                rows = cur.fetchall()
                return [r["email"] for r in rows]
    finally:
        conn.close()

def set_recipients(emails: List[str]) -> None:
    ensure_table()
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE recipients;")
                if emails:
                    args_str = ",".join(["(%s)"] * len(emails))
                    cur.execute("INSERT INTO recipients (email) VALUES " + args_str, emails)
    finally:
        conn.close()

def add_recipient(email: str) -> None:
    ensure_table()
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO recipients (email) VALUES (%s) ON CONFLICT DO NOTHING;", (email,))
    finally:
        conn.close()

def delete_recipient(email: str) -> None:
    ensure_table()
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM recipients WHERE email = %s;", (email,))
    finally:
        conn.close()