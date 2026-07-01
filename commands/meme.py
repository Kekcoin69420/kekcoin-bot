"""Meme submission pipeline — /meme offering + admin moderation."""
import re
from telegram import Update
from telegram.ext import ContextTypes

import db_supabase as sb
from config import ADMIN_IDS, WEBSITE_URL
from commands.admin import is_admin


def _slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:80] or "meme-offering")


def _parse_meme_args(text: str) -> tuple[str, str, str | None, str]:
    """Parse 'Title | summary | optional_url' or 'Title | summary'."""
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 2:
        raise ValueError("need_title_and_summary")
    title = parts[0][:120]
    summary = parts[1][:500]
    img_url = None
    cat = "modern"
    if len(parts) >= 3 and parts[2]:
        third = parts[2]
        if third.startswith("http"):
            img_url = third[:500]
        else:
            cat = third[:32]
    if len(parts) >= 4 and parts[3].startswith("http"):
        img_url = parts[3][:500]
    return title, summary, img_url, cat


async def _upload_photo(ctx: ContextTypes.DEFAULT_TYPE, file_id: str, slug: str) -> str | None:
    try:
        tg_file = await ctx.bot.get_file(file_id)
        data = await tg_file.download_as_bytearray()
        ext = "jpg"
        if tg_file.file_path and "." in tg_file.file_path:
            ext = tg_file.file_path.rsplit(".", 1)[-1].lower()[:4] or "jpg"
        return sb.upload_submission_image(slug, bytes(data), ext)
    except Exception:
        return None


async def cmd_meme(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg:
        return

    if not sb.is_configured():
        await msg.reply_text(
            "The offering altar is not wired to Supabase yet. "
            "Admins: set SUPABASE_URL and SUPABASE_SERVICE_KEY on Railway."
        )
        return

    body = " ".join(ctx.args) if ctx.args else ""
    if msg.reply_to_message and msg.reply_to_message.caption and not body:
        body = msg.reply_to_message.caption

    if not body or "|" not in body:
        await msg.reply_text(
            "𓂀 <b>Offer a Meme to the Archive</b> 𓂀\n\n"
            "<b>Text:</b> <code>/meme Title | summary</code>\n"
            "<b>With image URL:</b> <code>/meme Title | summary | https://…</code>\n"
            "<b>With category:</b> <code>/meme Title | summary | frog</code>\n"
            "<b>Photo:</b> reply to an image with <code>/meme Title | Temple lore</code>\n\n"
            "Images are re-encoded server-side — EXIF/GPS metadata stripped before storage.\n"
            "Categories: frog, classic, wojak, reaction, crypto, 4chan, modern\n"
            "Mods review offerings before they enter the Sacred Archive.",
            parse_mode="HTML",
        )
        return

    try:
        title, summary, img_url, cat = _parse_meme_args(body)
    except ValueError:
        await msg.reply_text("Use: /meme Title | summary  (pipe separator required)")
        return

    slug = _slugify(title)
    user = update.effective_user
    display = (user.full_name or user.username or "Pilgrim")[:40]

    if msg.reply_to_message and msg.reply_to_message.photo and not img_url:
        photo = msg.reply_to_message.photo[-1]
        uploaded = await _upload_photo(ctx, photo.file_id, slug)
        if uploaded:
            img_url = uploaded

    if img_url and img_url.startswith("http") and not sb.is_temple_hosted_url(img_url):
        rehosted = sb.fetch_and_sanitize_image(img_url, slug)
        if rehosted:
            img_url = rehosted
        else:
            await msg.reply_text(
                "Could not fetch or sanitize that image URL. "
                "Use a direct image link (jpg/png/webp/gif, under 5 MB) or reply to a photo."
            )
            return

    row = sb.submit_meme(
        slug=slug,
        title=title,
        summary=summary,
        lore=summary,
        cat=cat,
        img_url=img_url,
        telegram_user_id=user.id,
        telegram_username=user.username,
        display_name=display,
    )
    if not row:
        await msg.reply_text("The offering could not be recorded. Try again, pilgrim.")
        return

    sid = str(row.get("id", ""))[:8]
    await msg.reply_text(
        f"𓂀 Offering received — <b>{title}</b>\n"
        f"ID: <code>{sid}</code> · pending mod review\n"
        f"When approved it joins the archive and Codex.",
        parse_mode="HTML",
    )


async def cmd_pendingmemes(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not sb.is_configured():
        await update.message.reply_text("Supabase not configured.")
        return
    rows = sb.list_pending_memes(12)
    if not rows:
        await update.message.reply_text("No pending meme offerings.")
        return
    lines = []
    for r in rows:
        sid = str(r["id"])[:8]
        who = r.get("display_name") or r.get("telegram_username") or "anon"
        lines.append(f"• <code>{sid}</code> — <b>{r['title']}</b> ({who})")
    await update.message.reply_text(
        "𓂀 <b>Pending Offerings</b> 𓂀\n\n" + "\n".join(lines)
        + "\n\n/approvememe &lt;id&gt; · /rejectmeme &lt;id&gt; [reason]",
        parse_mode="HTML",
    )


async def cmd_approvememe(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /approvememe <submission_id_prefix>")
        return
    if not sb.is_configured():
        await update.message.reply_text("Supabase not configured.")
        return

    prefix = ctx.args[0].strip().lower()
    meme = sb.approve_meme(prefix, update.effective_user.id)
    if not meme:
        await update.message.reply_text("Submission not found or already reviewed.")
        return

    link = f"{WEBSITE_URL}memes/#{meme['id']}"
    codex = f"{WEBSITE_URL}codex/#{meme['id']}"
    await update.message.reply_text(
        f"✅ <b>{meme['title']}</b> inscribed in the archive.\n"
        f"<a href=\"{link}\">Archive</a> · <a href=\"{codex}\">Codex</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def cmd_rejectmeme(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /rejectmeme <id> [reason]")
        return
    prefix = ctx.args[0].strip().lower()
    reason = " ".join(ctx.args[1:])[:200] if len(ctx.args) > 1 else None
    if sb.reject_meme(prefix, update.effective_user.id, reason):
        await update.message.reply_text(f"Offering <code>{prefix}</code> rejected.", parse_mode="HTML")
    else:
        await update.message.reply_text("Submission not found or already reviewed.")