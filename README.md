# Kekcoin Telegram Bot

$KEK community bot — price commands, whale alerts, anti-FUD, daily digests.

## Setup

1. Copy `.env.example` to `.env` and fill in values
2. `pip install -r requirements.txt`
3. `python bot.py`

## Deployment (Railway)

1. Push to GitHub
2. New Railway project → deploy from GitHub
3. Add environment variables (see `.env.example`)
4. Add Volume mounted at `/data`
5. Railway auto-detects `Procfile` — uses `worker: python bot.py`

## Bot Permissions Required in Group

Make the bot an admin with:
- Delete messages
- Restrict members
- Pin messages

## Commands

| Command | Description |
|---|---|
| `/price` | Live $KEK price |
| `/stats` | Full stats including holders |
| `/ca` | Contract address |
| `/chart` | DexScreener link |
| `/buy` | Buy instructions |
| `/ath` | All-time high |
| `/praise` | Praise Kek |
| `/kek` | Random lore |
| `/moonmath [amount]` | Bag value calculator |
| `/hodlcheck [price]` | P&L from entry price |
| `/setwhale [usd]` | Admin: set whale threshold |
| `/addfud [keyword]` | Admin: add FUD keyword |
| `/removefud [keyword]` | Admin: remove FUD keyword |
| `/listfud` | Admin: list FUD keywords |
| `/announce [text]` | Admin: post announcement |
| `/warn` | Admin: reply to warn user |
| `/ban` | Admin: reply to ban user |
| `/setstrike [n]` | Admin: set mute threshold |
