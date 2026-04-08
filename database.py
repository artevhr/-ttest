"""
database.py — вся работа с SQLite.
"""
import aiosqlite
import datetime
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            joined_at   TEXT,
            last_seen   TEXT
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            subject     TEXT,
            test_type   TEXT,
            year        TEXT,
            stage       TEXT,
            variant     TEXT,
            primary_score INTEGER,
            test_score    INTEGER,
            max_primary   INTEGER,
            done_at       TEXT
        );

        CREATE TABLE IF NOT EXISTS ads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            is_active   INTEGER DEFAULT 0,
            photo_url   TEXT,
            channel_url TEXT,
            channel_name TEXT,
            ad_text     TEXT,
            countdown   INTEGER DEFAULT 5
        );
        """)
        await db.commit()


async def upsert_user(user_id: int, username: str, first_name: str):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, joined_at, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_seen  = excluded.last_seen
        """, (user_id, username, first_name, now, now))
        await db.commit()


async def touch_user(user_id: int):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_seen=? WHERE user_id=?", (now, user_id))
        await db.commit()


async def save_result(user_id, subject, test_type, year, stage, variant,
                      primary_score, test_score, max_primary):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO test_results
            (user_id,subject,test_type,year,stage,variant,primary_score,test_score,max_primary,done_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (user_id, subject, test_type, year, stage, variant,
              primary_score, test_score, max_primary, now))
        await db.commit()


# ── Статистика ──────────────────────────────────────────────
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        total_users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        today = datetime.date.today().isoformat()
        active_today = (await (await db.execute(
            "SELECT COUNT(*) FROM users WHERE last_seen LIKE ?", (today + "%",)
        )).fetchone())[0]
        tests_done = (await (await db.execute("SELECT COUNT(*) FROM test_results")).fetchone())[0]
    return {"total_users": total_users, "active_today": active_today, "tests_done": tests_done}


# ── Реклама ─────────────────────────────────────────────────
async def get_active_ad():
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT * FROM ads WHERE is_active=1 ORDER BY id DESC LIMIT 1"
        )).fetchone()
        if row:
            keys = ["id", "is_active", "photo_url", "channel_url", "channel_name", "ad_text", "countdown"]
            return dict(zip(keys, row))
    return None


async def upsert_ad(photo_url, channel_url, channel_name, ad_text, countdown=5):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE ads SET is_active=0")
        await db.execute("""
            INSERT INTO ads (is_active, photo_url, channel_url, channel_name, ad_text, countdown)
            VALUES (1,?,?,?,?,?)
        """, (photo_url, channel_url, channel_name, ad_text, countdown))
        await db.commit()


async def set_ad_active(state: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE ads SET is_active=?", (1 if state else 0,))
        await db.commit()
