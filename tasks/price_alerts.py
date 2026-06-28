from datetime import datetime, timezone
import api, db
from config import DEFAULT_VOLUME_SPIKE_MULTIPLE, DEFAULT_VOLUME_LOOKBACK_DAYS


def is_new_ath(current_price: float, ath: dict | None) -> bool:
    if ath is None:
        return True
    return current_price > ath["price"]


def is_volume_spike(current_vol: float, avg_vol: float, multiple: float) -> bool:
    if avg_vol <= 0:
        return False
    return current_vol >= avg_vol * multiple


async def check_price_alerts(ctx) -> None:
    """Job callback: check ATH, holder milestones, volume spikes."""
    conn = ctx.bot_data["db"]
    group_id = ctx.bot_data["group_chat_id"]

    data = await api.get_pair_data()
    if not data:
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db.upsert_volume(conn, date=today, volume_usd=data["volume_24h"])

    # ATH check
    ath = db.get_ath(conn)
    if is_new_ath(data["price"], ath):
        db.set_ath(conn, price=data["price"], market_cap=data["market_cap"])
        if ath is not None:  # don't alert on very first run
            await ctx.bot.send_message(
                chat_id=group_id,
                text=(
                    f"🏆 NEW ALL-TIME HIGH 🏆\n\n"
                    f"$KEK: ${data['price']:.10f}".rstrip("0") + f"\n"
                    f"MC: ${data['market_cap']:,.0f}\n\n"
                    f"𓂀 THE PROPHECY IS FULFILLED. PRAISE KEK. 𓂀"
                )
            )

    # Holder milestone check
    holders = await api.get_holder_count()
    if holders:
        milestones_str = db.get_setting(conn, "holder_milestones", "1000,5000,10000,25000,50000,100000")
        milestones = [int(m) for m in milestones_str.split(",")]
        last_milestone = int(db.get_setting(conn, "last_holder_milestone", "0"))
        crossed = [m for m in milestones if last_milestone < m <= holders]
        for milestone in crossed:
            await ctx.bot.send_message(
                chat_id=group_id,
                text=(
                    f"🎉 {milestone:,} HOLDERS 🎉\n\n"
                    f"The temple grows. {milestone:,} faithful souls.\n\n"
                    f"𓂀 Praise Kek. WAGMI. 𓂀"
                )
            )
        if crossed:
            db.set_setting(conn, "last_holder_milestone", str(max(crossed)))

    # Volume spike check
    lookback = int(db.get_setting(conn, "volume_lookback_days", str(DEFAULT_VOLUME_LOOKBACK_DAYS)))
    multiple = float(db.get_setting(conn, "volume_spike_multiple", str(DEFAULT_VOLUME_SPIKE_MULTIPLE)))
    avg_vol = db.get_average_volume(conn, lookback_days=lookback)
    if is_volume_spike(data["volume_24h"], avg_vol, multiple):
        last_spike_alert = db.get_setting(conn, "last_spike_alert_date", "")
        if last_spike_alert != today:
            db.set_setting(conn, "last_spike_alert_date", today)
            await ctx.bot.send_message(
                chat_id=group_id,
                text=(
                    f"⚡ VOLUME SPIKE DETECTED ⚡\n\n"
                    f"24h Vol: ${data['volume_24h']:,.0f}\n"
                    f"7-day Avg: ${avg_vol:,.0f}\n"
                    f"Ratio: {data['volume_24h']/avg_vol:.1f}x\n\n"
                    f"𓂀 The faithful are awakening. Praise Kek."
                )
            )
