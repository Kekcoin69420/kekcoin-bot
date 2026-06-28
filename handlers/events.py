from telegram import Update, ChatMemberUpdated, ChatMember
from telegram.ext import ContextTypes
from config import CA, JUPITER_URL, DEXSCREENER_CHART_URL


def _is_new_member(update: ChatMemberUpdated) -> bool:
    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    return old_status in (ChatMember.LEFT, ChatMember.BANNED) and \
           new_status in (ChatMember.MEMBER, ChatMember.RESTRICTED)


async def welcome_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    member_update = update.chat_member
    if not member_update or not _is_new_member(member_update):
        return

    user = member_update.new_chat_member.user
    name = user.first_name or "faithful one"

    await ctx.bot.send_message(
        chat_id=member_update.chat.id,
        text=(
            f"𓂀 A new soul enters the Temple of Kek 𓂀\n\n"
            f"Welcome, {name}! You have found the sacred coin.\n\n"
            f"$KEK — The first dogecoin derivative.\n"
            f"Born on 4chan's /s4s/. Community-owned since Dec 11, 2025.\n\n"
            f"📜 CA: `{CA}`\n"
            f"⚡ [Buy on Jupiter]({JUPITER_URL})\n"
            f"📊 [View Chart]({DEXSCREENER_CHART_URL})\n\n"
            f"Praise Kek and HODL. 𓆏"
        ),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
