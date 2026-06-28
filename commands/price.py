from telegram import Update
from telegram.ext import ContextTypes
import api
import db
from config import CA, JUPITER_URL, PUMPFUN_URL, DEXSCREENER_CHART_URL


def _fmt_usd(n: float) -> str:
    if n >= 1e9: return f"${n/1e9:.2f}B"
    if n >= 1e6: return f"${n/1e6:.2f}M"
    if n >= 1e3: return f"${n/1e3:.1f}K"
    if n >= 1: return f"${n:.4f}"
    # tiny price: find leading zeros
    s = f"{n:.10f}".rstrip("0")
    return s if s.startswith("$") else f"${s.lstrip('$')}"


def fmt_price(data: dict) -> str:
    chg = data["change_24h"]
    arrow = "📈" if chg >= 0 else "📉"
    sign = "+" if chg >= 0 else ""
    return (
        f"𓂀 THE ORACLE SPEAKS 𓂀\n\n"
        f"$KEK — {_fmt_usd(data['price'])}\n"
        f"{arrow} {sign}{chg:.2f}% (24h)\n\n"
        f"MC: {_fmt_usd(data['market_cap'])} | "
        f"Vol: {_fmt_usd(data['volume_24h'])} | "
        f"Liq: {_fmt_usd(data['liquidity'])}\n\n"
        f"Redeemable for one ounce of comedy gold."
    )


def fmt_stats(data: dict, holders: int | None = None) -> str:
    chg = data["change_24h"]
    sign = "+" if chg >= 0 else ""
    holder_str = f"{holders:,}" if holders else "—"
    return (
        f"📊 $KEK STATS\n\n"
        f"Price: {_fmt_usd(data['price'])} ({sign}{chg:.2f}%)\n"
        f"Market Cap: {_fmt_usd(data['market_cap'])}\n"
        f"Liquidity: {_fmt_usd(data['liquidity'])}\n"
        f"24h Volume: {_fmt_usd(data['volume_24h'])}\n"
        f"24h Txns: {data['txns_24h']:,}\n"
        f"Holders: {holder_str}\n\n"
        f"𓂀 Praise Kek 𓂀"
    )


def build_ca_message() -> str:
    return (
        f"📜 $KEK CONTRACT ADDRESS\n\n"
        f"`{CA}`\n\n"
        f"⚡ [Buy on Jupiter]({JUPITER_URL})\n"
        f"🔥 [Buy on Pump.fun]({PUMPFUN_URL})\n\n"
        f"Always verify the CA before buying. 𓂀"
    )


async def cmd_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    data = await api.get_pair_data()
    if not data:
        await update.message.reply_text("⚠️ The oracle is silent. Try again shortly.")
        return
    await update.message.reply_text(fmt_price(data))


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    data = await api.get_pair_data()
    if not data:
        await update.message.reply_text("⚠️ The oracle is silent. Try again shortly.")
        return
    holders = await api.get_holder_count()
    await update.message.reply_text(fmt_stats(data, holders))


async def cmd_ca(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(build_ca_message(), parse_mode="Markdown", disable_web_page_preview=True)


async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"📊 [View $KEK Chart on DexScreener]({DEXSCREENER_CHART_URL})\n\nPraise Kek 𓂀",
        parse_mode="Markdown"
    )


async def cmd_buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"⚡ HOW TO BUY $KEK\n\n"
        f"1. Install Phantom wallet\n"
        f"2. Buy SOL on any exchange and send to your wallet\n"
        f"3. Swap on [Jupiter]({JUPITER_URL}) or [Pump.fun]({PUMPFUN_URL})\n\n"
        f"CA: `{CA}`\n\n"
        f"𓆏 Join the cult. Praise Kek.",
        parse_mode="Markdown", disable_web_page_preview=True
    )


async def cmd_ath(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    conn = ctx.bot_data["db"]
    ath = db.get_ath(conn)
    if not ath:
        await update.message.reply_text("No ATH recorded yet — the oracle is still watching.")
        return
    await update.message.reply_text(
        f"🏆 $KEK ALL-TIME HIGH\n\n"
        f"Price: {_fmt_usd(ath['price'])}\n"
        f"Market Cap: {_fmt_usd(ath['market_cap'])}\n"
        f"Recorded: {ath['recorded_at'][:10]}\n\n"
        f"𓂀 Will we see it again? Praise Kek."
    )
