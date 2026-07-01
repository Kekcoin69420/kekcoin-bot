"""Lexicon command: /define <term> — reads Temple Lexicon from Supabase REST."""
import logging

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from config import SUPABASE_URL, SUPABASE_ANON_KEY

log = logging.getLogger(__name__)
COLS = "id,term,cat,definition,origin,related,aka"
TIMEOUT = 10.0


def _headers() -> dict:
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }


def _get(path: str, params: dict | None = None) -> list[dict]:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return []
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(url, headers=_headers(), params=params or {})
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
    except Exception as e:
        log.warning("define _get failed: %s", e)
        return []


def _lookup(query: str) -> dict | None:
    """Match by id (slug), exact term, alias (aka array), then partial term."""
    words = (query or "").strip()
    if not words:
        return None
    slug = words.lower().replace(" ", "-")
    low = words.lower()

    rows = _get("lexicon", {"select": COLS, "id": f"eq.{slug}", "limit": "1"})
    if rows:
        return rows[0]

    rows = _get("lexicon", {"select": COLS, "term": f"ilike.{words}", "limit": "1"})
    if rows:
        return rows[0]

    rows = _get("lexicon", {"select": COLS, "aka": f"cs.{{{low}}}", "limit": "1"})
    if rows:
        return rows[0]

    rows = _get("lexicon", {"select": COLS, "term": f"ilike.*{words}*", "limit": "1"})
    return rows[0] if rows else None


def _terms() -> list[str]:
    rows = _get("lexicon", {"select": "term", "order": "term.asc"})
    return [x["term"] for x in rows if x.get("term")]


def _format(row: dict) -> str:
    term = row.get("term") or row["id"]
    definition = (row.get("definition") or "").strip()
    origin = (row.get("origin") or "").strip()
    related = row.get("related") or []
    lines = ["𓂀 THE LEXICON 𓂀", term.lower(), "", definition]
    if origin:
        lines += ["", f"origin: {origin}"]
    if related:
        lines += ["", "see also: " + ", ".join(related)]
    return "\n".join(lines)


async def cmd_define(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(ctx.args).strip() if ctx.args else ""
    if not query:
        terms = _terms()
        sample = ", ".join(terms[:16])
        await update.message.reply_text(
            "𓂀 THE LEXICON 𓂀\n\n"
            "speak a word and the temple will define it:  /define based\n\n"
            f"the lexicon holds {len(terms)} words, among them:\n{sample} ..."
        )
        return
    row = _lookup(query)
    if not row:
        await update.message.reply_text(
            f"𓂀 the lexicon does not yet hold \u201c{query}\u201d.\n"
            "try /define kek, /define wagmi, or /define rizz."
        )
        return
    await update.message.reply_text(_format(row))