# 𓂀 Kekcoin Telegram Bot

The official community bot for [$KEK](https://kekcoin69420.github.io/kekcoin/) — the first dogecoin derivative, born on 4chan's /s4s/, community-owned since December 11, 2025.

[![Twitter](https://img.shields.io/badge/Twitter-@kekcoin69420-1DA1F2?logo=twitter)](https://x.com/kekcoin69420)
[![Telegram](https://img.shields.io/badge/Telegram-Join%20the%20Temple-2CA5E0?logo=telegram)](https://t.me/kekcoincto_tg)

---

## What it does

- **Live price & chart** — real-time candlestick chart images (15m candles) from on-chain data
- **Whale alerts** — automatic alerts when large buys or sells hit the pair
- **Anti-FUD** — auto-deletes FUD messages, strikes repeat offenders, auto-mutes at threshold
- **Daily digest** — 9am UTC price and stats summary posted to the group
- **Community commands** — praise counter, lore, moon math, P&L calculator
- **Admin tools** — warn, ban, announce, configure thresholds

---

## Commands

### Price
| Command | Description |
|---|---|
| `/price` | Live price with 24h change, MC, volume |
| `/stats` | Full stats including holder count and txns |
| `/chart` | Candlestick chart image (15m candles) |
| `/ca` | Contract address |
| `/buy` | How to buy instructions |
| `/ath` | All-time high price and market cap |
| `/links` | All official links in one place |

### Community
| Command | Description |
|---|---|
| `/praise` | Offer praise to Kek (with milestones) |
| `/kek` | Random $KEK lore quote |
| `/moonmath [amount]` | Bag value at various MC targets |
| `/hodlcheck [entry price]` | Your P&L from entry price |
| `/prophecy` | The sacred prophecy of the Temple |
| `/ritual` | The ritual to enter the Temple |
| `/help` or `/h` | List all commands (admins see admin ones too) |
| `/about` | Temple intro |
| `/lore` | Deeper lore from the canon |
| `/initiate` | Guide for new members |
| `/relic` | The coin as sacred relic |
| `/fud` | Current fud keywords watched |
| `/praiseboard` | Top praisers |
| `/whale` | Current whale threshold |
| `/voice` | Random voice of the Temple |
| `/canon` | The seven sacred truths |

See the [kekcoin-temple-core](https://github.com/Kekcoin69420/kekcoin-temple-core) repo for full lore, voice system, rituals, and blueprints. The bot integrates the Temple canon.

### Admin only
| Command | Description |
|---|---|
| `/setwhale [usd]` | Set whale alert threshold |
| `/addfud [keyword]` | Add a FUD keyword to auto-delete |
| `/removefud [keyword]` | Remove a FUD keyword |
| `/listfud` | List all active FUD keywords |
| `/announce [text]` | Post a group announcement |
| `/warn` | Reply to a message to warn that user |
| `/ban` | Reply to a message to ban that user |
| `/setstrike [n]` | Set auto-mute threshold (default: 3) |

---

## Stack

- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21
- [httpx](https://www.python-httpx.org/) for async HTTP
- [mplfinance](https://github.com/matplotlib/mplfinance) for chart generation
- SQLite for state persistence
- Deployed on [Railway](https://railway.app)

---

## Self-hosting

### 1. Clone and install

```bash
git clone https://github.com/Kekcoin69420/kekcoin-bot.git
cd kekcoin-bot
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```
BOT_TOKEN=your_bot_token_from_botfather
GROUP_CHAT_ID=-1001234567890
ADMIN_IDS=123456789,987654321
HELIUS_API_KEY=your_helius_key
DB_PATH=./data/kek.db
```

### 3. Run

```bash
python bot.py
```

### Bot permissions required in group

Make the bot an admin with:
- Delete messages
- Restrict members

---

## Deploy to Railway

1. Fork this repo
2. New Railway project → Deploy from GitHub → select your fork
3. Add environment variables (see `.env.example`)
4. Add a Railway Volume mounted at `/data`
5. Railway auto-detects the `Procfile`

---

## Contract

```
BY4ttYDiMWsyBebNNjNoSfA3krvZvUaPaaYdJsWmpump
```

Always verify the CA before buying. 𓂀

---

## License

MIT — fork it, run your own, build on it. Praise Kek.
