"""Meme Bible commands: /bible <meme> and /scripture.

Recites the Temple's Meme Bible from the shared Supabase `memes` table
(the `scripture` column). Single-file drop-in:

  1. Save this as  commands/bible.py
  2. In bot.py, import and register the two handlers (see INTEGRATION.md).

No new dependencies: it reuses the same Supabase client db_supabase.py already
uses for the praise board, so it works as soon as SUPABASE_URL /
SUPABASE_SERVICE_KEY are set (and degrades silently if they are not).
"""
import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

from db_supabase import _get_client
from config import WEBSITE_URL

log = logging.getLogger(__name__)

# Full entries live here on the site. Repoint to WEBSITE_URL + "codex/" once a
# dedicated codex page ships; for now it links into the meme archive.
CODEX_BASE = WEBSITE_URL + "memes/"
MAX_LEN = 3500  # keep under Telegram's 4096-char message cap
COLS = "id,title,year,tier,kek,summary,scripture,source_url"


def _lookup(query: str):
    """Find one meme by id (slug), then by title, preferring rows with scripture."""
    sb = _get_client()
    if not sb:
        return None
    words = (query or "").strip()
    slug = words.lower().replace(" ", "-")
    try:
        r = sb.table("memes").select(COLS).eq("id", slug).limit(1).execute()
        if r.data:
            return r.data[0]
        r = (sb.table("memes").select(COLS)
             .ilike("title", f"%{words}%")
             .filter("scripture", "not.is", "null").limit(1).execute())
        if r.data:
            return r.data[0]
        r = sb.table("memes").select(COLS).ilike("title", f"%{words}%").limit(1).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        log.warning("bible _lookup failed: %s", e)
        return None


def _random():
    sb = _get_client()
    if not sb:
        return None
    try:
        r = (sb.table("memes").select(COLS)
             .filter("scripture", "not.is", "null").execute())
        rows = r.data or []
        return random.choice(rows) if rows else None
    except Exception as e:
        log.warning("bible _random failed: %s", e)
        return None


def _titles():
    sb = _get_client()
    if not sb:
        return []
    try:
        r = (sb.table("memes").select("id,title")
             .filter("scripture", "not.is", "null").order("title").execute())
        return [(x["id"], x["title"]) for x in (r.data or [])]
    except Exception:
        return []


def _format(row: dict) -> str:
    title = (row.get("title") or row["id"]).upper()
    tier = row.get("tier") or ""
    year = row.get("year")
    kek = int(row.get("kek") or 0)
    source = row.get("source_url")
    body = (row.get("scripture") or row.get("summary")
            or "the canon does not yet record this relic.").strip()
    if len(body) > MAX_LEN:
        body = body[:MAX_LEN].rsplit(" ", 1)[0] + " ..."

    sub = "  ·  ".join(b for b in [tier, str(year) if year else None] if b)
    lines = ["𓂀 THE MEME BIBLE 𓂀", title]
    if sub:
        lines.append(sub)
    lines += ["", body, ""]
    if kek:
        lines.append("kek-rating: " + ("𓂀" * kek) + f"  ({kek}/5)")
    lines.append(f"📜 the codex: {CODEX_BASE}#{row['id']}")
    if source:
        lines.append(f"the record: {source}")
    return "\n".join(lines)


async def cmd_bible(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(ctx.args).strip() if ctx.args else ""
    if not query:
        titles = _titles()
        sample = ", ".join(t for _, t in titles[:12])
        await update.message.reply_text(
            "𓂀 THE MEME BIBLE 𓂀\n\n"
            "speak the name of a relic:  /bible pepe\n\n"
            f"the codex holds {len(titles)} relics, among them:\n{sample}\n\n"
            "or call /scripture for a random verse."
        )
        return
    row = _lookup(query)
    if not row:
        await update.message.reply_text(
            f"𓂀 the codex does not yet record \u201c{query}\u201d.\n"
            "try /bible pepe, /bible doge, or /scripture for a random verse."
        )
        return
    await update.message.reply_text(_format(row))


async def cmd_scripture(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    row = _random()
    if not row:
        await update.message.reply_text("𓂀 the codex is silent. (no scripture configured.)")
        return
    await update.message.reply_text(_format(row))
