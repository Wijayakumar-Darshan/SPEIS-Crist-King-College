"""security.py – Activity logging and simple security utilities."""
import database as db
from datetime import datetime


def log_activity(user_id: int, action: str):
    try:
        db.run_query(
            "INSERT INTO activity_logs (user_id, action, ts) VALUES (?,?,?)",
            (user_id, action, datetime.now().isoformat()),
        )
    except Exception:
        pass


def get_recent_logs(limit: int = 50):
    return db.run_query(
        """SELECT l.*, u.username, u.role
           FROM activity_logs l
           LEFT JOIN users u ON l.user_id = u.id
           ORDER BY l.ts DESC LIMIT ?""",
        (limit,), fetch=True,
    )
