"""Supabase sync for praise board + meme submission pipeline.
Falls back silently if SUPABASE_URL / SUPABASE_SERVICE_KEY are not set,
so the bot keeps working even before Supabase is configured.
"""
import logging
import re
import uuid
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

log = logging.getLogger(__name__)
_client = None

CAT_TIERS = {
    "frog": "Sacred", "classic": "Legendary", "wojak": "Legendary",
    "reaction": "Modern", "crypto": "Modern", "4chan": "Ancient", "modern": "Modern",
}


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)


def _slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:80] or "meme-offering"


def _scripture_from(row: dict) -> str:
    lore = (row.get("lore") or "").strip()
    summary = (row.get("summary") or "").strip()
    desc = (row.get("description") or "").strip()
    if lore and desc and lore != desc:
        return lore + "\n\n" + desc
    if lore:
        return lore
    if desc:
        return desc
    return summary


def _unique_slug(sb, base: str) -> str:
    slug = base
    n = 2
    while True:
        res = sb.table("memes").select("id").eq("id", slug).limit(1).execute()
        if not res.data:
            return slug
        slug = f"{base}-{n}"
        n += 1


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


def upload_submission_image(slug: str, data: bytes, ext: str = "jpg") -> str | None:
    """Upload bytes to public meme-submissions bucket. Returns public URL."""
    sb = _get_client()
    if not sb:
        return None
    safe = re.sub(r"[^\w-]", "", slug)[:60] or str(uuid.uuid4())[:8]
    path = f"{safe}.{ext}"
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/jpeg")
    try:
        sb.storage.from_("meme-submissions").upload(
            path, data,
            file_options={"content-type": mime, "upsert": "true"},
        )
        return f"{SUPABASE_URL}/storage/v1/object/public/meme-submissions/{path}"
    except Exception as e:
        log.warning("upload_submission_image failed: %s", e)
        return None


def submit_meme(
    slug: str,
    title: str,
    summary: str,
    lore: str,
    cat: str,
    img_url: str | None,
    telegram_user_id: int,
    telegram_username: str | None,
    display_name: str,
) -> dict | None:
    sb = _get_client()
    if not sb:
        return None
    cat = (cat or "modern").lower()
    if cat not in CAT_TIERS:
        cat = "modern"
    try:
        res = sb.table("meme_submissions").insert({
            "slug": slug,
            "title": title,
            "summary": summary,
            "lore": lore or summary,
            "description": summary,
            "cat": cat,
            "img_url": img_url,
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
            "display_name": display_name,
            "status": "pending",
        }).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        log.warning("submit_meme failed: %s", e)
        return None


def list_pending_memes(limit: int = 12) -> list:
    sb = _get_client()
    if not sb:
        return []
    try:
        res = (
            sb.table("meme_submissions")
            .select("id,title,slug,display_name,telegram_username,created_at")
            .eq("status", "pending")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        log.warning("list_pending_memes failed: %s", e)
        return []


def _find_submission(sb, prefix: str) -> dict | None:
    prefix = prefix.lower().strip()
    try:
        res = (
            sb.table("meme_submissions")
            .select("*")
            .eq("status", "pending")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        for row in res.data or []:
            if str(row["id"]).lower().startswith(prefix):
                return row
    except Exception as e:
        log.warning("_find_submission failed: %s", e)
    return None


def approve_meme(prefix: str, admin_id: int) -> dict | None:
    sb = _get_client()
    if not sb:
        return None
    sub = _find_submission(sb, prefix)
    if not sub:
        return None
    base_slug = _slugify(sub.get("slug") or sub["title"])
    meme_id = _unique_slug(sb, base_slug)
    cat = sub.get("cat") or "modern"
    row = {
        "id": meme_id,
        "title": sub["title"],
        "summary": sub.get("summary") or "",
        "description": sub.get("description") or sub.get("summary") or "",
        "lore": sub.get("lore") or sub.get("summary") or "",
        "cat": cat,
        "tier": CAT_TIERS.get(cat, "Modern"),
        "kek": 3,
        "img": sub.get("img_url"),
        "scripture": _scripture_from(sub),
        "source_url": f"https://www.kektemple.com/memes/#{meme_id}",
    }
    try:
        sb.table("memes").upsert(row, on_conflict="id").execute()
        sb.table("meme_submissions").update({
            "status": "approved",
            "reviewed_by": admin_id,
            "reviewed_at": "now()",
            "approved_meme_id": meme_id,
        }).eq("id", sub["id"]).execute()
        return row
    except Exception as e:
        log.warning("approve_meme failed: %s", e)
        return None


def reject_meme(prefix: str, admin_id: int, reason: str | None = None) -> bool:
    sb = _get_client()
    if not sb:
        return False
    sub = _find_submission(sb, prefix)
    if not sub:
        return False
    try:
        sb.table("meme_submissions").update({
            "status": "rejected",
            "reviewed_by": admin_id,
            "reviewed_at": "now()",
            "reject_reason": reason,
        }).eq("id", sub["id"]).execute()
        return True
    except Exception as e:
        log.warning("reject_meme failed: %s", e)
        return False
