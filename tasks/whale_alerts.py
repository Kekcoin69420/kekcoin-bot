import api, db
from config import DEFAULT_WHALE_THRESHOLD


def should_alert(usd_value: float, threshold: float) -> bool:
    return usd_value >= threshold


async def check_whale_alerts(ctx) -> None:
    """Job callback: poll recent txns, alert on whales."""
    conn = ctx.bot_data["db"]
    group_id = ctx.bot_data["group_chat_id"]
    threshold = float(db.get_setting(conn, "whale_threshold_usd", str(DEFAULT_WHALE_THRESHOLD)))

    data = await api.get_pair_data()
    if not data:
        return

    last_sig = db.get_whale_state(conn)
    signatures = await api.get_recent_signatures(limit=20)
    if not signatures:
        return

    # Process only new signatures (stop at last_seen)
    new_sigs = []
    for sig_info in signatures:
        if sig_info["signature"] == last_sig:
            break
        new_sigs.append(sig_info["signature"])

    if not new_sigs:
        return

    # Update last seen
    db.set_whale_state(conn, signatures[0]["signature"])

    for sig in new_sigs[:5]:  # cap at 5 to avoid flood
        tx = await api.get_transaction(sig)
        result = api.parse_swap_usd(tx, data["price"])
        if not result:
            continue
        usd_value, direction = result
        if not should_alert(usd_value, threshold):
            continue

        wallet = sig[:4] + "..." + sig[-4:]
        emoji = "🐋" if direction == "buy" else "🔴"
        action = "purchased" if direction == "buy" else "sold"
        footer = "𓂀 Praise Kek 𓂀" if direction == "buy" else "The temple endures. HODL."

        await ctx.bot.send_message(
            chat_id=group_id,
            text=(
                f"{emoji} WHALE SPOTTED {emoji}\n\n"
                f"{'A true believer enters the temple.' if direction == 'buy' else 'A soul has departed.'}\n\n"
                f"💰 ${usd_value:,.0f} of $KEK {action}\n"
                f"📈 Price: ${data['price']:.10f}".rstrip("0") + f"\n"
                f"🔗 Tx: {wallet}\n\n"
                f"{footer}"
            )
        )
