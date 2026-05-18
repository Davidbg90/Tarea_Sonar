import sqlite3
from datetime import datetime
import config


def get_conn():
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                set_name TEXT DEFAULT '',
                card_number TEXT DEFAULT '',
                quantity INTEGER DEFAULT 1,
                condition TEXT DEFAULT 'NM',
                language TEXT DEFAULT 'ES',
                foil INTEGER DEFAULT 0,
                price_low REAL,
                price_trend REAL,
                price_avg REAL,
                price_avg1 REAL,
                price_avg7 REAL,
                price_avg30 REAL,
                last_updated TEXT,
                pokemontcg_id TEXT,
                image_url TEXT DEFAULT '',
                image_url_large TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                price_low REAL,
                price_trend REAL,
                price_avg REAL,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS update_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                cards_updated INTEGER DEFAULT 0,
                status TEXT DEFAULT 'ok',
                message TEXT DEFAULT ''
            );
        """)
    _migrate()


def _migrate():
    """Add columns that may not exist in older DBs."""
    new_cols = {
        "price_avg1": "REAL",
        "price_avg7": "REAL",
        "price_avg30": "REAL",
        "image_url_large": "TEXT DEFAULT ''",
        "pokemontcg_id": "TEXT",
    }
    with get_conn() as conn:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(cards)")}
        for col, typ in new_cols.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE cards ADD COLUMN {col} {typ}")
        conn.commit()


def get_all_cards():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM cards ORDER BY name").fetchall()]


def get_card(card_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
        return dict(row) if row else None


def add_card(name, set_name='', card_number='', quantity=1,
             condition='NM', language='ES', foil=False,
             pokemontcg_id=None, image_url='', image_url_large=''):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO cards (name, set_name, card_number, quantity, condition,
                               language, foil, pokemontcg_id, image_url, image_url_large)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, set_name, card_number, quantity, condition,
              language, int(bool(foil)), pokemontcg_id, image_url, image_url_large))
        conn.commit()


def update_card(card_id, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [card_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE cards SET {fields} WHERE id=?", values)
        conn.commit()


def delete_card(card_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM cards WHERE id=?", (card_id,))
        conn.commit()


def update_prices(prices_by_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        for card_id, p in prices_by_id.items():
            conn.execute("""
                UPDATE cards SET
                    price_low=?, price_trend=?, price_avg=?,
                    price_avg1=?, price_avg7=?, price_avg30=?,
                    image_url=?, image_url_large=?, last_updated=?
                WHERE id=?
            """, (p.get("price_low"), p.get("price_trend"), p.get("price_avg"),
                  p.get("price_avg1"), p.get("price_avg7"), p.get("price_avg30"),
                  p.get("image_url", ""), p.get("image_url_large", ""), now, card_id))
            # Record in price history (only if we got at least a trend price)
            if p.get("price_trend") or p.get("price_avg"):
                conn.execute("""
                    INSERT INTO price_history (card_id, recorded_at, price_low, price_trend, price_avg)
                    VALUES (?, ?, ?, ?, ?)
                """, (card_id, now, p.get("price_low"), p.get("price_trend"), p.get("price_avg")))
        conn.commit()


def get_price_history(card_id, limit=30):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("""
            SELECT recorded_at, price_low, price_trend, price_avg
            FROM price_history
            WHERE card_id=?
            ORDER BY id DESC LIMIT ?
        """, (card_id, limit)).fetchall()]


def get_collection_stats():
    with get_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) as total_cards,
                SUM(quantity) as total_quantity,
                SUM(COALESCE(price_trend, price_low, price_avg, 0) * quantity) as total_value
            FROM cards
        """).fetchone()
        return dict(row) if row else {}


def log_update(cards_updated, status='ok', message=''):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO update_log (cards_updated, status, message)
            VALUES (?, ?, ?)
        """, (cards_updated, status, message))
        conn.commit()


def get_last_update():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT updated_at, status, message FROM update_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
