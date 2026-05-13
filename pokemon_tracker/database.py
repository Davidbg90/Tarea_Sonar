import sqlite3
from datetime import datetime
import config


def get_conn():
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
                last_updated TEXT,
                cardmarket_id INTEGER,
                image_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS update_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                cards_updated INTEGER DEFAULT 0,
                status TEXT DEFAULT 'ok',
                message TEXT DEFAULT ''
            );
        """)


def get_all_cards():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM cards ORDER BY name"
        ).fetchall()]


def get_card(card_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
        return dict(row) if row else None


def add_card(name, set_name='', card_number='', quantity=1,
             condition='NM', language='ES', foil=False,
             cardmarket_id=None, image_url=''):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO cards (name, set_name, card_number, quantity, condition,
                               language, foil, cardmarket_id, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, set_name, card_number, quantity, condition,
              language, int(bool(foil)), cardmarket_id, image_url))
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
    """prices_by_id: {card_id: {'price_low': x, 'price_trend': y, 'price_avg': z}}"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        for card_id, prices in prices_by_id.items():
            conn.execute("""
                UPDATE cards
                SET price_low=?, price_trend=?, price_avg=?, last_updated=?
                WHERE id=?
            """, (prices.get("price_low"), prices.get("price_trend"),
                  prices.get("price_avg"), now, card_id))
        conn.commit()


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
