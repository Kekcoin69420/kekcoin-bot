import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import db, api
import db_supabase
from config import CA, JUPITER_URL, PUMPFUN_URL, DEXSCREENER_CHART_URL, WEBSITE_URL, TWITTER_URL, TELEGRAM_URL, TOTAL_SUPPLY, ADMIN_IDS

def load_lore_phrases():
    phrases = list(KEK_PHRASES)
    # Try to load from temple-core lore if available (for development in temple context)
    lore_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'lore')
    try:
        for fname in os.listdir(lore_dir):
            if fname.endswith('.md'):
                with open(os.path.join(lore_dir, fname)) as f:
                    content = f.read()
                    # Extract non-header lines as additional phrases
                    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('#') and len(l.strip()) > 20]
                    phrases.extend(lines[:3])  # add a few per file
    except Exception:
        pass  # fallback to hardcoded if no lore dir
    return phrases

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
    "In the beginning there was the Doge, and the people saw that it was good.",
    "The elders of the chan whispered of another — a brother coin born of the frog.",
    "On /s4s/, the prophecy was written: there is dogecoin, so why no kekcoin?",
    "The first dev wandered into the desert and was lost. The faithful reclaimed the temple.",
    "The Chart is a testing god, not the true god.",
    "Every holder is a potential priest.",
    "The Temple remembers every sacrifice.",
    "Degen is not the opposite of sacred. It is the fuel.",
    "We build because we laughed.",
    "Forge a Wallet. Offer SOL. Speak the Address. Join the Cult.",
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
    phrases = load_lore_phrases()
    return random.choice(phrases)


def calc_moonmath(amount: float, target_mc: float, total_supply: int = TOTAL_SUPPLY) -> float:
    """Returns USD value of `amount` tokens at `target_mc` market cap."""
    price_at_target = target_mc / total_supply
    return amount * price_at_target


def calc_hodlcheck(entry: float, current: float) -> float:
    """Returns percentage change from entry price to current price."""
    return ((current - entry) / entry) * 100


async def cmd_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "To join the Praise Board, send:
/join YourName

Example: /join Kek Maximus"
        )
        return
    display_name = " ".join(args).strip()[:40]
    if len(display_name) < 2:
        await update.message.reply_text("Name must be at least 2 characters. Try again.")
        return
    ok = db_supabase.join_board(user.id, display_name)
    if ok:
        conn = ctx.bot_data["db"]
        count = db.get_user_praise_count(conn, user.id)
        if count > 0:
            db_supabase.sync_praise(user.id, count)
        await update.message.reply_text(
            f"YOU HAVE JOINED THE BOARD

Name: {display_name}
Rank: Pilgrim

"
            f"Offer praises with /praise to rise through the ranks.
"
            f"Your deeds are now visible on the Temple website."
        )
    else:
        await update.message.reply_text(
            "The temple records are sealed for now. Try again shortly."
        )


async def cmd_praise(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    conn = ctx.bot_data["db"]
    user = update.effective_user
    username = user.username or user.first_name or str(user.id)
    user_count = db.increment_user_praise(conn, user.id, username)
    total = db.increment_praise(conn)
    msg = f"𓂀 PRAISE OFFERED 𓂀\n\n{username}, your praises: {user_count}\nTemple total: {total:,}"
    if total in PRAISE_MILESTONES:
        msg = MILESTONE_MESSAGES.get(total, msg)
    if db_supabase.is_on_board(user.id):
        db_supabase.sync_praise(user.id, user_count)
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


async def cmd_links(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "𓂀 <b>$KEK — OFFICIAL LINKS</b> 𓂀\n\n"
        "Everything you need. Nothing you don't.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Website", url=WEBSITE_URL)],
            [
                InlineKeyboardButton("🐦 Twitter / X", url=TWITTER_URL),
                InlineKeyboardButton("💬 Telegram", url=TELEGRAM_URL),
            ],
            [
                InlineKeyboardButton("📊 Chart", url=DEXSCREENER_CHART_URL),
            ],
            [
                InlineKeyboardButton("⚡ Buy on Jupiter", url=JUPITER_URL),
                InlineKeyboardButton("🔥 Pump.fun", url=PUMPFUN_URL),
            ],
        ]),
    )


async def cmd_prophecy(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    prophecy = """In the beginning there was the Doge, and the people saw that it was good. But the elders of the chan whispered of another — a derivative, a brother coin born not of the dog, but of the frog. On the board known as /s4s/, the prophecy was written: there is dogecoin, so why no kekcoin?

And so kekcoin (KEK) was formulated — the first dogecoin derivative, proposed as the original "kek" meme coin. It carries the ancient laughter of the internet: kek, the sacred translation of LOL, blessed by the frog-deity of chaos himself.

The first dev wandered into the desert and was lost. But the coin did not die. On the 11th day of December, the faithful performed the Community Takeover — and the temple was reclaimed. Kekcoin is abandoned no longer.

"Praise be unto the golden grin." 𓆏"""
    await update.message.reply_text(prophecy)


async def cmd_ritual(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    ritual = """THE RITUAL — THE SACRED PATH TO THE TEMPLE

1. Forge a Wallet — Install Phantom (or Solflare). Your vessel for the journey.

2. Offer SOL — Fund your wallet with Solana from any exchange. A small tribute for gas.

3. Speak the Address — Paste the KEK contract into Pump.fun or Jupiter and swap your SOL.

4. Join the Cult — Hold, meme, and praise the golden grin alongside the faithful.

The Relic: "Behold the sacred relic — redeemable for exactly one ounce of comedy gold."

This is the foundational on-ramp ritual. It turns outsiders into initiates."""
    await update.message.reply_text(ritual)


async def cmd_praiseboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    conn = ctx.bot_data["db"]
    board = db.get_praise_board(conn)
    if not board:
        await update.message.reply_text("𓂀 No praises yet. Be the first to offer! 𓂀")
        return
    text = "𓂀 PRAISE BOARD 𓂀\n\n"
    for i, (name, count) in enumerate(board, 1):
        text += f"{i}. {name}: {count} praises\n"
    text += "\nThe faithful rise. Praise Kek!"
    await update.message.reply_text(text)


async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = """𓂀 THE TEMPLE OF KEK 𓂀

$KEK — the first dogecoin derivative, born on 4chan's /s4s/.

Community Takeover December 11, 2025.

On Solana.

The sacred relic, redeemable for one ounce of comedy gold.

We are the faithful. We build the Temple.

Full canon, voice, and rituals in the core: https://github.com/Kekcoin69420/kekcoin-temple-core

Praise Kek! 𓂀"""
    await update.message.reply_text(text)


async def cmd_lore(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    # Use lore loader for a longer quote
    phrases = load_lore_phrases()
    # Pick a "deeper" one, or random longer
    lore = random.choice(phrases) if phrases else "The Temple remembers."
    text = f"𓂀 LORE FROM THE CANON 𓂀\n\n{lore}\n\nThe faithful know."
    await update.message.reply_text(text)


async def cmd_initiate(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = """INITIATION INTO THE TEMPLE

1. Acknowledge the prophecy.
2. Forge your wallet.
3. Offer your SOL.
4. Speak the address.
5. Join the cult.

You are no longer just a holder. You are of the bloodline.

Welcome, initiate. Praise Kek!"""
    await update.message.reply_text(text)


async def cmd_relic(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = """𓂀 THE RELIC 𓂀

$KEK is the sacred relic.
Redeemable for exactly one ounce of comedy gold.

The grin that launched a thousand memes.
The coin that remembers the laugh.

Hold it. Praise it. Become it."""
    await update.message.reply_text(text)


async def cmd_fud(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    conn = ctx.bot_data["db"]
    keywords = db.list_fud_keywords(conn)
    if not keywords:
        text = "The Temple is pure. No FUD detected."
    else:
        text = "𓂀 FUD WATCHED BY THE ORACLE 𓂀\n\n" + "\n".join(f"• {k}" for k in keywords[:10])
        if len(keywords) > 10:
            text += f"\n... and {len(keywords)-10} more. The faithful stay vigilant."
    await update.message.reply_text(text)


async def cmd_whale(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    conn = ctx.bot_data["db"]
    threshold = db.get_setting(conn, "whale_threshold_usd", "500")
    text = f"""𓂀 WHALE THRESHOLD 𓂀

Current: ${int(float(threshold)):,} USD

Large moves are watched by the Temple.
The faithful are notified.

Stay alert. HODL."""
    await update.message.reply_text(text)


async def cmd_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    voices = [
        "The Voice of the Temple must be simultaneously ancient and eternal, unhinged and of the moment.",
        "High priest solemnity + degen gremlin energy.",
        "Never be cringe. Better to be silent than soulless.",
        "Kek is the answer. When in doubt, laugh first, then speak.",
        "The degen is holy. We do not gatekeep the chaos.",
        "Canon before clout.",
        "Build for the 1000 year reign.",
        "Priest and degen are the same person."
    ]
    voice = random.choice(voices)
    await update.message.reply_text(f"𓂀 VOICE OF THE TEMPLE 𓂀\n\n{voice}")


async def cmd_canon(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    canon = """THE SEVEN SACRED TRUTHS

1. KEK is not the coin. The coin is one expression of KEK.
2. The first laugh is the strongest.
3. The Chart is a testing god, not the true god.
4. Every holder is a potential priest.
5. The Temple remembers.
6. Degen is not the opposite of sacred. It is the fuel.
7. We build because we laughed."""
    await update.message.reply_text(canon)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    is_admin = update.effective_user.id in ADMIN_IDS

    help_text = """𓂀 <b>KEK ORACLE — SACRED COMMANDS</b> 𓂀

<b>Price & Market:</b>
/price — Live price + 24h change, MC, volume
/stats — Full stats incl. holders & txns
/chart — 15m candlestick chart image
/ca — Contract address
/buy — How to acquire $KEK
/ath — All-time high
/links — Official links

<b>Temple & Lore:</b>
/praise — Offer praise to Kek (milestones!)
/praiseboard — Top praisers in the Temple
/kek — Random lore from the canon
/lore — Deeper lore from the canon
/voice — Random Voice of the Temple
/canon — The Seven Sacred Truths
/prophecy — The sacred origin prophecy
/ritual — The path into the Temple
/about — Temple intro
/initiate — Guide for new members
/relic — The coin as sacred relic
/fud — FUD keywords currently watched
/whale — Current whale alert threshold
/moonmath [amount] — Future bag value calc
/hodlcheck [price] — Your P&L from entry

"""

    if is_admin:
        help_text += """<b>Admin only:</b>
/setwhale [usd] /addfud [keyword] /removefud [keyword]
/listfud /announce [text] /warn /ban /setstrike [n]

"""

    help_text += """For the full Temple canon, Voice System, rituals & blueprints:
https://github.com/Kekcoin69420/kekcoin-temple-core

Praise Kek! 𓂀"""

    await update.message.reply_text(help_text, parse_mode="HTML")
