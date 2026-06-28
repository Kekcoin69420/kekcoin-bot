from datetime import datetime, timezone, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
import db


def contains_fud(text: str, keywords: list[str]) -> bool:
    """Returns True if text contains any FUD keyword (case-insensitive, partial match)."""
    lower = text.lower()
    return any(kw in lower for kw in keywords)


async def antifud_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.text:
        return

    conn = ctx.bot_data["db"]
    keywords = db.list_fud_keywords(conn)

    if not contains_fud(msg.text, keywords):
        return

    user = msg.from_user
    group_id = ctx.bot_data["group_chat_id"]

    # Delete the offending message
    try:
        await ctx.bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    except Exception:
        pass  # may fail if already deleted

    # Add strike
    count = db.add_strike(conn, user_id=user.id, username=user.username or str(user.id))
    threshold = int(db.get_setting(conn, "strike_mute_threshold", default="3"))

    name = f"@{user.username}" if user.username else user.first_name

    if count >= threshold:
        # Auto-mute for 24h
        until = int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())
        try:
            await ctx.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_audios=False,
                    can_send_documents=False,
                    can_send_photos=False,
                    can_send_videos=False,
                    can_send_video_notes=False,
                    can_send_voice_notes=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                ),
                until_date=until
            )
        except Exception:
            pass

        # Notify admins
        for admin_id in ctx.bot_data.get("admin_ids", []):
            try:
                await ctx.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ Auto-muted {name} for 24h after {count} FUD strikes."
                )
            except Exception:
                pass

        await ctx.bot.send_message(
            chat_id=msg.chat.id,
            text=f"🚫 {name} has been muted for 24h. The temple is cleansed. 𓂀"
        )
    else:
        await ctx.bot.send_message(
            chat_id=msg.chat.id,
            text=f"𓂀 The temple does not welcome FUD. The faithful hold.\n\n"
                 f"{name}: strike {count}/{threshold}."
        )
