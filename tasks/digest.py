import random
from datetime import datetime, timezone
import api, db
from commands.community import KEK_PHRASES


async def send_daily_digest(ctx) -> None:
    """Job callback: post daily price summary at configured hour."""
    conn = ctx.bot_data["db"]
    group_id = ctx.bot_data["group_chat_id"]

    data = await api.get_pair_data()
    holders = await api.get_holder_count()

    if not data:
        return

    chg = data["change_24h"]
    sign = "+" if chg >= 0 else ""
    arrow = "📈" if chg >= 0 else "📉"
    holder_str = f"{holders:,}" if holders else "—"

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db.upsert_volume(conn, date=today, volume_usd=data["volume_24h"])

    quote = random.choice(KEK_PHRASES)

    await ctx.bot.send_message(
        chat_id=group_id,
        text=(
            f"🌅 DAILY DIGEST — {today}\n\n"
            f"$KEK: ${data['price']:.10f}".rstrip("0") + f"\n"
            f"{arrow} {sign}{chg:.2f}% (24h)\n"
            f"MC: ${data['market_cap']:,.0f}\n"
            f"Vol: ${data['volume_24h']:,.0f}\n"
            f"Holders: {holder_str}\n\n"
            f"— {quote}\n\n"
            f"𓂀 Praise Kek 𓂀"
        )
    )
