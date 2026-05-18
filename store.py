"""
store.py - Fixed with permanent post ID tracking + active post DB storage
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "jayesh_agent.db"

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                post_text           TEXT    NOT NULL,
                pillar              TEXT,
                format              TEXT,
                topic               TEXT,
                keywords_used       TEXT,
                hashtags_used       TEXT,
                sources             TEXT,
                status              TEXT    DEFAULT 'draft',
                generated_at        TEXT,
                sent_to_whatsapp_at TEXT,
                approved_at         TEXT,
                posted_at           TEXT,
                linkedin_post_id    TEXT,
                feedback            TEXT,
                impressions         INTEGER DEFAULT 0,
                day_of_week         INTEGER
            )
        """)
        # ── NEW: Active post tracking table ──────────────
        # Survives server restarts unlike in-memory variables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_state (
                key   TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weekly_stats (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start      TEXT,
                posts_generated INTEGER DEFAULT 0,
                posts_approved  INTEGER DEFAULT 0,
                posts_posted    INTEGER DEFAULT 0,
                posts_rejected  INTEGER DEFAULT 0,
                posts_skipped   INTEGER DEFAULT 0,
                total_impressions INTEGER DEFAULT 0,
                created_at      TEXT
            )
        """)
        conn.commit()
    print("[Store] DB initialised.")

# ── Active Post Tracking (survives restarts) ───────────────

def set_active_post(post_id: int):
    """Save active pending post ID to DB — survives server restarts."""
    with _conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO agent_state (key, value, updated_at)
            VALUES ('active_post_id', ?, ?)
        """, (str(post_id), datetime.now().isoformat()))
        conn.commit()
    print(f"[Store] Active post set: #{post_id}")

def get_active_post_id() -> int | None:
    """Get active pending post ID from DB."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT value FROM agent_state WHERE key = 'active_post_id'"
        ).fetchone()
        if row and row["value"]:
            return int(row["value"])
    return None

def clear_active_post():
    """Clear active post after it's been handled."""
    with _conn() as conn:
        conn.execute(
            "DELETE FROM agent_state WHERE key = 'active_post_id'"
        )
        conn.commit()

# ── Post CRUD ──────────────────────────────────────────────

def save_draft(post: dict) -> int:
    with _conn() as conn:
        cur = conn.execute("""
            INSERT INTO posts (
                post_text, pillar, format, topic,
                keywords_used, hashtags_used, sources,
                status, generated_at, day_of_week
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
        """, (
            post.get("post_text",""),
            post.get("pillar",""),
            post.get("format",""),
            post.get("topic",""),
            json.dumps(post.get("keywords_used",[])),
            json.dumps(post.get("hashtags_used",[])),
            json.dumps(post.get("sources",[])),
            post.get("generated_at", datetime.now().isoformat()),
            datetime.now().weekday(),
        ))
        conn.commit()
        return cur.lastrowid

def update_status(post_id: int, status: str, **kwargs):
    allowed = {"linkedin_post_id","feedback","impressions",
               "sent_to_whatsapp_at","approved_at","posted_at"}
    sets = ["status = ?"]
    vals = [status]
    if status == "posted" and "posted_at" not in kwargs:
        sets.append("posted_at = ?")
        vals.append(datetime.now().isoformat())
    if status == "approved" and "approved_at" not in kwargs:
        sets.append("approved_at = ?")
        vals.append(datetime.now().isoformat())
    for k, v in kwargs.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            vals.append(v)
    vals.append(post_id)
    with _conn() as conn:
        conn.execute(
            f"UPDATE posts SET {', '.join(sets)} WHERE id = ?", vals
        )
        conn.commit()

def update_post_text(post_id: int, new_text: str):
    with _conn() as conn:
        conn.execute(
            "UPDATE posts SET post_text = ?, status = 'draft' WHERE id = ?",
            (new_text, post_id)
        )
        conn.commit()

def get_post(post_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        return dict(row) if row else None

def get_latest_pending() -> dict | None:
    """Get most recently WhatsApp-sent post — never picks old drafts."""
    with _conn() as conn:
        # Priority 1: active post from DB state
        active_id = get_active_post_id()
        if active_id:
            row = conn.execute(
                "SELECT * FROM posts WHERE id = ?", (active_id,)
            ).fetchone()
            if row and dict(row).get("status") not in ("posted","rejected","failed"):
                return dict(row)

        # Priority 2: most recently WhatsApp-sent
        row = conn.execute("""
            SELECT * FROM posts
            WHERE status = 'whatsapp_sent'
            ORDER BY sent_to_whatsapp_at DESC, id DESC
            LIMIT 1
        """).fetchone()
        if row:
            return dict(row)

        # Priority 3: most recent draft (last resort)
        row = conn.execute("""
            SELECT * FROM posts
            WHERE status = 'draft'
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        return dict(row) if row else None

def get_all_posts(limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_recent_topics(limit: int = 30) -> list[str]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT topic, keywords_used FROM posts ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        topics = []
        for r in rows:
            if r["topic"]:
                topics.append(r["topic"].lower())
            try:
                kw = json.loads(r["keywords_used"] or "[]")
                topics.extend([k.lower() for k in kw])
            except Exception:
                pass
        return topics

def get_recent_hashtags(limit: int = 7) -> list[str]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT hashtags_used FROM posts ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        tags = []
        for r in rows:
            try:
                tags.extend(json.loads(r["hashtags_used"] or "[]"))
            except Exception:
                pass
        return tags

def get_recent_pillars(limit: int = 5) -> list[str]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT pillar FROM posts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [r["pillar"] for r in rows if r["pillar"]]

def get_week_stats() -> dict:
    with _conn() as conn:
        from datetime import timedelta
        today      = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        rows = conn.execute("""
            SELECT status, COUNT(*) as cnt FROM posts
            WHERE DATE(generated_at) >= ?
            GROUP BY status
        """, (week_start.isoformat(),)).fetchall()
        stats = {
            "week_start":      week_start.isoformat(),
            "posts_generated": 0,
            "posts_posted":    0,
            "posts_approved":  0,
            "posts_rejected":  0,
            "posts_skipped":   0,
        }
        for r in rows:
            stats["posts_generated"] += r["cnt"]
            key = f"posts_{r['status']}"
            if key in stats:
                stats[key] = r["cnt"]
        return stats

if __name__ == "__main__":
    init_db()
    print("[Store] Ready.")
