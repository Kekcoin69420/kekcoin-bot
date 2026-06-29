"""Supabase sync for the live praise board on the website.
Falls back silently if SUPABASE_URL / SUPABASE_SERVICE_KEY are not set,
so the bot keeps working even before Supabase is configured.
"""
import logging
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

log = logging.getLogger(__name__)
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        log.warning("Supabase client init failed: %s", e)
    return _client


def join_board(telegram_id: int, display_name: str, role: str = "Pilgrim") -> bool:
    """Add or update a member on the praise board. Returns True on success."""
    sb = _get_client()
    if not sb:
        return False
    try:
        sb.table("praise_board").upsert({
            "telegram_id": telegram_id,
            "display_name": display_name[:40],
            "role": role,
        }, on_conflict="telegram_id").execute()
        return True
    except Exception as e:
        log.warning("Supabase join_board failed: %s", e)
        return False


def sync_praise(telegram_id: int, praise_count: int) -> bool:
    """Push the latest local praise count to Supabase for a member who has joined."""
    sb = _get_client()
    if not sb:
        return False
    try:
        sb.table("praise_board") \
          .update({"praise_count": praise_count, "updated_at": "now()"}) \
          .eq("telegram_id", telegram_id) \
          .execute()
        return True
    except Exception as e:
        log.warning("Supabase sync_praise failed: %s", e)
        return False


def is_on_board(telegram_id: int) -> bool:
    """Check if a user has joined the board."""
    sb = _get_client()
    if not sb:
        return False
    try:
        res = sb.table("praise_board").select("telegram_id").eq("telegram_id", telegram_id).execute()
        return len(res.data) > 0
    except Exception:
        return False
