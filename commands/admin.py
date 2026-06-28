from telegram import Update
from telegram.ext import ContextTypes
import db
from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def cmd_setwhale(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /setwhale [amount in USD]\nExample: /setwhale 1000")
        return
    try:
        amount = float(ctx.args[0])
        assert amount > 0
    except (ValueError, AssertionError):
        await update.message.reply_text("Please provide a valid positive number.")
        return
    conn = ctx.bot_data["db"]
    db.set_setting(conn, "whale_threshold_usd", str(amount))
    await update.message.reply_text(f"🐋 Whale threshold set to ${amount:,.0f}")


async def cmd_addfud(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /addfud [keyword]")
        return
    keyword = " ".join(ctx.args).lower()
    conn = ctx.bot_data["db"]
    db.add_fud_keyword(conn, keyword, added_by=update.effective_user.id)
    await update.message.reply_text(f"✅ Added FUD keyword: `{keyword}`", parse_mode="Markdown")


async def cmd_removefud(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /removefud [keyword]")
        return
    keyword = " ".join(ctx.args).lower()
    conn = ctx.bot_data["db"]
    db.remove_fud_keyword(conn, keyword)
    await update.message.reply_text(f"🗑️ Removed FUD keyword: `{keyword}`", parse_mode="Markdown")


async def cmd_listfud(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    conn = ctx.bot_data["db"]
    keywords = db.list_fud_keywords(conn)
    if not keywords:
        await update.message.reply_text("No FUD keywords configured.")
        return
    await update.message.reply_text("🚫 FUD Keywords:\n\n" + "\n".join(f"• {k}" for k in keywords))


async def cmd_announce(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /announce [message]")
        return
    text = " ".join(ctx.args)
    await ctx.bot.send_message(
        chat_id=ctx.bot_data["group_chat_id"],
        text=f"📢 TEMPLE ANNOUNCEMENT\n\n{text}\n\n𓂀 Praise Kek 𓂀"
    )


async def cmd_warn(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to warn that user.")
        return
    target = update.message.reply_to_message.from_user
    conn = ctx.bot_data["db"]
    count = db.add_strike(conn, user_id=target.id, username=target.username or str(target.id))
    threshold = int(db.get_setting(conn, "strike_mute_threshold", default="3"))
    await update.message.reply_text(
        f"⚠️ @{target.username or target.first_name} warned. Strikes: {count}/{threshold}"
    )


async def cmd_ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to ban that user.")
        return
    target = update.message.reply_to_message.from_user
    group_id = ctx.bot_data["group_chat_id"]
    await ctx.bot.ban_chat_member(chat_id=group_id, user_id=target.id)
    await update.message.reply_text(f"🔨 {target.first_name} has been banished from the temple.")


async def cmd_setstrike(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /setstrike [number]\nExample: /setstrike 3")
        return
    try:
        n = int(ctx.args[0])
        assert n > 0
    except (ValueError, AssertionError):
        await update.message.reply_text("Please provide a positive integer.")
        return
    conn = ctx.bot_data["db"]
    db.set_setting(conn, "strike_mute_threshold", str(n))
    await update.message.reply_text(f"⚙️ Auto-mute threshold set to {n} strikes.")
