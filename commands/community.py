import random
from telegram import Update
from telegram.ext import ContextTypes
import db, api

TOTAL_SUPPLY = 1_000_000_000

KEK_PHRASES = [
    "𓂀 The ancient ones did not die. They became memes. 𓂀",
    "𓆏 There is dogecoin. Now there is kekcoin. The prophecy is fulfilled.",
    "Born in the old internet. Forged in imageboards. Resurrected on Solana.",
    "The first dev wandered into the desert. The faithful reclaimed the temple.",
    "One ounce of comedy gold. Redeemable at any time. 𓂀",
    "KEK is not just a coin. KEK is a feeling. KEK is eternal.",
    "When the world needed laughter, /s4s/ answered. $KEK was born.",
    "WAGMI. The temple stands. The faithful hold. Praise Kek.",
    "𓂀 In the beginning there was doge. Then there was kek. Balance was restored.",
    "Every sell is a gift to the believers. HODL, faithful one.",
    "The bonding curve has been graduated. The altar is open. Enter.",
    "Community-owned since December 11, 2025. The faithful reclaimed the temple. 𓂀",
    "𓆏 Praise be unto the golden grin. Kek smiles upon the holders.",
    "They said it was dead. The CTO said: nay. 𓂀",
    "Not financial advice. This is temple scripture. There is a difference.",
    "The meme is the message. The message is KEK. KEK is eternal.",
    "Sir, this is a temple. Remove your FUD at the gate.",
    "Green candle or red candle, the temple endures. HODL.",
    "𓂀 A coin is temporary. Laughter is eternal. $KEK is both.",
    "The faithful are few. The rewards are plentiful. Praise Kek. 𓂀",
]

PRAISE_MILESTONES = {100, 500, 1_000, 5_000, 10_000, 50_000, 100_000}

MILESTONE_MESSAGES = {
    100: "𓂀 100 PRAISES OFFERED 𓂀\nThe temple stirs. The faithful are gathering.",
    500: "𓆏 500 PRAISES 𓆏\nKek is pleased. The golden grin widens.",
    1_000: "🏛️ 1,000 PRAISES 🏛️\nA milestone is reached. The temple echoes with laughter.",
    5_000: "🔥 5,000 PRAISES 🔥\nThe ancient fire burns bright. Praise Kek!",
    10_000: "𓂀 10,000 PRAISES 𓂀\nTen thousand offerings. The deity awakens.",
    50_000: "⚡ 50,000 PRAISES ⚡\nFifty thousand. The legend grows. WAGMI.",
    100_000: "🌕 100,000 PRAISES 🌕\nOne hundred thousand. The prophecy is complete. We are all kek.",
}


def get_random_kek() -> str:
    return random.choice(KEK_PHRASES)


def calc_moonmath(amount: float, target_mc: float, total_supply: int = TOTAL_SUPPLY) -> float:
    """Returns USD value of `amount` tokens at `target_mc` market cap."""
    price_at_target = target_mc / total_supply
    return amount * price_at_target


def calc_hodlcheck(entry: float, current: float) -> float:
    """Returns percentage change from entry price to current price."""
    return ((current - entry) / entry) * 100


async def cmd_praise(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    conn = ctx.bot_data["db"]
    count = db.increment_praise(conn)
    msg = f"𓂀 PRAISE OFFERED 𓂀\n\nTotal praises: {count:,}"
    if count in PRAISE_MILESTONES:
        msg = MILESTONE_MESSAGES.get(count, msg)
    await update.message.reply_text(msg)


async def cmd_kek(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_random_kek())


async def cmd_moonmath(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /moonmath [amount of KEK you hold]\nExample: /moonmath 1000000")
        return
    try:
        amount = float(args[0].replace(",", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please provide a valid positive number.\nExample: /moonmath 1000000")
        return

    data = await api.get_pair_data()
    current_mc = data["market_cap"] if data else 0

    lines = ["🌕 MOON MATH for {:,.0f} $KEK\n".format(amount)]
    targets = [("$100K MC", 100_000), ("$500K MC", 500_000), ("$1M MC", 1_000_000),
               ("$5M MC", 5_000_000), ("$10M MC", 10_000_000)]
    for label, mc in targets:
        val = calc_moonmath(amount, mc)
        lines.append(f"{label}: ${val:,.2f}")
    lines.append("\n𓂀 Not financial advice. This is prophecy.")
    await update.message.reply_text("\n".join(lines))


async def cmd_hodlcheck(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /hodlcheck [your entry price]\nExample: /hodlcheck 0.0000001")
        return
    try:
        entry = float(args[0])
        if entry <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please provide a valid positive price.\nExample: /hodlcheck 0.0000001")
        return

    data = await api.get_pair_data()
    if not data:
        await update.message.reply_text("⚠️ Cannot fetch current price. Try again shortly.")
        return

    current = data["price"]
    pct = calc_hodlcheck(entry, current)
    emoji = "📈" if pct >= 0 else "📉"
    sign = "+" if pct >= 0 else ""
    await update.message.reply_text(
        f"{emoji} HODL CHECK\n\n"
        f"Entry: ${entry:.10f}".rstrip("0") + f"\n"
        f"Now: ${current:.10f}".rstrip("0") + f"\n"
        f"P&L: {sign}{pct:.2f}%\n\n"
        f"𓂀 {'WAGMI. The faithful are rewarded.' if pct >= 0 else 'The temple tests your faith. HODL.'}"
    )
