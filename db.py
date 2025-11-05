## Handles all database operations

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_URL

def get_connection():
    conn = psycopg2.connect(DB_URL)
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Table to hold RSS feeds
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feeds (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            category TEXT,
            enabled BOOLEAN DEFAULT TRUE NOT NULL,
            added_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    # Articles
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            summary TEXT,
            ai_summary TEXT,
            published TIMESTAMP,
            sent BOOLEAN DEFAULT FALSE NOT NULL,
            UNIQUE(feed_id, link)
        )
    """)

    # Table to hold settings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

def get_feeds(enabled_only=True):
    conn = get_connection()
    cur = conn.cursor()
    if enabled_only:
        cur.execute("SELECT * FROM feeds WHERE enabled = TRUE ORDER BY added_at")
    else:
        cur.execute("SELECT * FROM feeds ORDER BY added_at")
    feeds = cur.fetchall()
    cur.close()
    conn.close()
    return feeds

def add_feed(url, category=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO feeds (url, category) VALUES (%s, %s) ON CONFLICT (url) DO NOTHING", (url, category))
    conn.commit()
    cur.close()
    conn.close()

def update_feed(feed_id, **kwargs):
    options = ["url", "category", "enabled"]
    updates = ", ".join(f"{k} = %s" for k in kwargs if k in options)
    values = [v for k, v in kwargs.items() if k in options]
    if not updates:
        return
    conn = get_connection()
    cur = conn.cursor()
    query = f"UPDATE feeds SET {updates} WHERE id = %s"
    cur.execute(query, values + [feed_id])
    conn.commit()
    cur.close()
    conn.close()

def delete_feed(feed_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM feeds WHERE id = %s", (feed_id,))
    conn.commit()
    cur.close()
    conn.close()

def article_exists(feed_id, link):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM articles WHERE feed_id = %s AND link = %s", (feed_id, link))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_article(feed_id, title, link, summary=None, ai_summary=None, published=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO articles (feed_id, title, link, summary, ai_summary, published)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (feed_id, link) DO NOTHING
    """, (feed_id, title, link, summary, ai_summary, published))
    conn.commit()
    cur.close()
    conn.close()

def get_setting(key, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = %s", (key,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else default

def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (key, value))
    conn.commit()
    cur.close()
    conn.close()