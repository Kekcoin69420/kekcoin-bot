import io
import matplotlib
matplotlib.use("Agg")
import pandas as pd
import mplfinance as mpf
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import api
import db
from config import CA, JUPITER_URL, PUMPFUN_URL, DEXSCREENER_CHART_URL


def _fmt_usd(n: float) -> str:
    if n >= 1e9: return f"${n/1e9:.2f}B"
    if n >= 1e6: return f"${n/1e6:.2f}M"
    if n >= 1e3: return f"${n/1e3:.1f}K"
    if n >= 1: return f"${n:.4f}"
    s = f"{n:.10f}".rstrip("0")
    return f"${s}"


def _price_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Buy on Jupiter", url=JUPITER_URL),
            InlineKeyboardButton("🔥 Pump.fun", url=PUMPFUN_URL),
        ],
        [
            InlineKeyboardButton("📊 Chart", url=DEXSCREENER_CHART_URL),
            InlineKeyboardButton("📜 Copy CA", callback_data="copy_ca"),
        ],
    ])


def fmt_price(data: dict) -> str:
    chg = data["change_24h"]
    arrow = "📈" if chg >= 0 else "📉"
    sign = "+" if chg >= 0 else ""
    bull = "🟢" if chg >= 0 else "🔴"
    return (
        f"𓂀 <b>THE ORACLE SPEAKS</b> 𓂀\n\n"
        f"<b>$KEK</b>  {_fmt_usd(data['price'])}\n"
        f"{bull} {arrow} <b>{sign}{chg:.2f}%</b> (24h)\n\n"
        f"<b>MC</b>   {_fmt_usd(data['market_cap'])}\n"
        f"<b>Vol</b>  {_fmt_usd(data['volume_24h'])}\n"
        f"<b>Liq</b>  {_fmt_usd(data['liquidity'])}\n\n"
        f"<i>Redeemable for one ounce of comedy gold.</i>"
    )


def fmt_stats(data: dict, holders: int | None = None) -> str:
    chg = data["change_24h"]
    sign = "+" if chg >= 0 else ""
    bull = "🟢" if chg >= 0 else "🔴"
    holder_str = f"{holders:,}" if holders else "—"
    sentiment = "Bullish 𓂀" if chg >= 0 else "The temple tests faith. HODL."
    return (
        f"📊 <b>$KEK STATS</b>\n\n"
        f"<b>Price:</b>     {_fmt_usd(data['price'])}  {bull} {sign}{chg:.2f}%\n"
        f"<b>Market Cap:</b> {_fmt_usd(data['market_cap'])}\n"
        f"<b>Liquidity:</b>  {_fmt_usd(data['liquidity'])}\n"
        f"<b>24h Volume:</b> {_fmt_usd(data['volume_24h'])}\n"
        f"<b>24h Txns:</b>   {data['txns_24h']:,}\n"
        f"<b>Holders:</b>    {holder_str}\n\n"
        f"<i>{sentiment}</i>"
    )


def build_ca_message() -> str:
    return (
        f"📜 <b>$KEK CONTRACT ADDRESS</b>\n\n"
        f"<code>{CA}</code>\n\n"
        f"Tap the address above to copy.\n"
        f"Always verify the CA before buying. 𓂀"
    )


def generate_chart_image(candles: list[dict], current_price: float) -> io.BytesIO | None:
    if not candles or len(candles) < 5:
        return None
    try:
        df = pd.DataFrame(candles)
        df["datetime"] = pd.to_datetime(df["time"], unit="s")
        df = df.set_index("datetime").sort_index()
        df = df.rename(columns={
            "open": "Open", "high": "High",
            "low": "Low", "close": "Close", "volume": "Volume"
        })[["Open", "High", "Low", "Close", "Volume"]]

        mc = mpf.make_marketcolors(
            up="#00e676", down="#ff1744",
            wick={"up": "#00e676", "down": "#ff1744"},
            volume={"up": "#00e67655", "down": "#ff174455"},
            edge="inherit",
        )
        style = mpf.make_mpf_style(
            base_mpf_style="nightclouds",
            marketcolors=mc,
            facecolor="#0d1117",
            edgecolor="#30363d",
            figcolor="#0d1117",
            gridcolor="#21262d",
            gridstyle="--",
            y_on_right=True,
        )

        buf = io.BytesIO()
        mpf.plot(
            df,
            type="candle",
            style=style,
            volume=True,
            title=f"\n$KEK / USD   {_fmt_usd(current_price)}   (15m candles)",
            figsize=(10, 6),
            savefig=dict(fname=buf, dpi=150, bbox_inches="tight"),
        )
        buf.seek(0)
        return buf
    except Exception:
        return None


async def cmd_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    data = await api.get_pair_data()
    if not data:
        await update.message.reply_text("⚠️ The oracle is silent. Try again shortly.")
        return
    await update.message.reply_text(
        fmt_price(data),
        parse_mode="HTML",
        reply_markup=_price_buttons(),
    )


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    data = await api.get_pair_data()
    if not data:
        await update.message.reply_text("⚠️ The oracle is silent. Try again shortly.")
        return
    holders = await api.get_holder_count()
    await update.message.reply_text(
        fmt_stats(data, holders),
        parse_mode="HTML",
        reply_markup=_price_buttons(),
    )


async def cmd_ca(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        build_ca_message(),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚡ Buy on Jupiter", url=JUPITER_URL),
                InlineKeyboardButton("🔥 Pump.fun", url=PUMPFUN_URL),
            ],
        ]),
    )


async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("📊 Generating chart...")
    data, candles = await api.get_pair_data(), await api.get_candles()
    image = generate_chart_image(candles, data["price"] if data else 0)

    if image:
        await msg.delete()
        caption = fmt_price(data) if data else "𓂀 $KEK Chart"
        await update.message.reply_photo(
            photo=image,
            caption=caption,
            parse_mode="HTML",
            reply_markup=_price_buttons(),
        )
    else:
        await msg.edit_text(
            f"📊 <a href='{DEXSCREENER_CHART_URL}'>View $KEK Chart on DexScreener</a>\n\nPraise Kek 𓂀",
            parse_mode="HTML",
            reply_markup=_price_buttons(),
        )


async def cmd_buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"⚡ <b>HOW TO BUY $KEK</b>\n\n"
        f"1. Install Phantom wallet\n"
        f"2. Buy SOL on any exchange and send to your wallet\n"
        f"3. Tap a button below to swap\n\n"
        f"<code>{CA}</code>\n\n"
        f"𓆏 Join the cult. Praise Kek.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚡ Buy on Jupiter", url=JUPITER_URL),
                InlineKeyboardButton("🔥 Buy on Pump.fun", url=PUMPFUN_URL),
            ],
        ]),
    )


async def cmd_ath(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    conn = ctx.bot_data["db"]
    ath = db.get_ath(conn)
    if not ath:
        await update.message.reply_text("No ATH recorded yet — the oracle is still watching.")
        return
    await update.message.reply_text(
        f"🏆 <b>$KEK ALL-TIME HIGH</b>\n\n"
        f"<b>Price:</b>      {_fmt_usd(ath['price'])}\n"
        f"<b>Market Cap:</b> {_fmt_usd(ath['market_cap'])}\n"
        f"<b>Recorded:</b>   {ath['recorded_at'][:10]}\n\n"
        f"<i>𓂀 Will we see it again? Praise Kek.</i>",
        parse_mode="HTML",
        reply_markup=_price_buttons(),
    )
