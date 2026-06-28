from telegram import Update, ChatMemberUpdated, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CA, JUPITER_URL, PUMPFUN_URL, DEXSCREENER_CHART_URL, WEBSITE_URL, TWITTER_URL, TELEGRAM_URL


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
            f"𓂀 <b>A new soul enters the Temple of Kek</b> 𓂀\n\n"
            f"Welcome, <b>{name}</b>! You have found the sacred coin.\n\n"
            f"<b>$KEK</b> — The first dogecoin derivative.\n"
            f"Born on 4chan's /s4s/. Community-owned since Dec 11, 2025.\n\n"
            f"<code>{CA}</code>\n\n"
            f"Type /price for the live price or /links for everything else.\n\n"
            f"Praise Kek and HODL. 𓆏"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚡ Buy on Jupiter", url=JUPITER_URL),
                InlineKeyboardButton("🔥 Pump.fun", url=PUMPFUN_URL),
            ],
            [
                InlineKeyboardButton("📊 Chart", url=DEXSCREENER_CHART_URL),
                InlineKeyboardButton("🌐 Website", url=WEBSITE_URL),
            ],
        ]),
    )
