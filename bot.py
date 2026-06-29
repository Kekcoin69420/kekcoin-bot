import logging
import os
from datetime import time, timezone

from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ChatMemberHandler, filters
)

import db
from config import (
    BOT_TOKEN, GROUP_CHAT_ID, ADMIN_IDS, DB_PATH,
    DEFAULT_DIGEST_HOUR_UTC
)
from commands.price import cmd_price, cmd_stats, cmd_ca, cmd_chart, cmd_buy, cmd_ath
from commands.community import cmd_praise, cmd_join, cmd_kek, cmd_moonmath, cmd_hodlcheck, cmd_links, cmd_prophecy, cmd_ritual, cmd_help, cmd_praiseboard, cmd_about, cmd_lore, cmd_initiate, cmd_relic, cmd_fud, cmd_whale, cmd_voice, cmd_canon
from commands.admin import (
    cmd_setwhale, cmd_addfud, cmd_removefud, cmd_listfud,
    cmd_announce, cmd_warn, cmd_ban, cmd_setstrike
)
from filters.antifud import antifud_handler
from handlers.events import welcome_handler
from tasks.whale_alerts import check_whale_alerts
from tasks.price_alerts import check_price_alerts
from tasks.digest import send_daily_digest

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def main() -> None:
    conn = db.init_db(DB_PATH)

    app = Application.builder().token(BOT_TOKEN).build()

    # Shared bot data
    app.bot_data["db"] = conn
    app.bot_data["group_chat_id"] = GROUP_CHAT_ID
    app.bot_data["admin_ids"] = ADMIN_IDS

    # Price commands
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("ca", cmd_ca))
    app.add_handler(CommandHandler("chart", cmd_chart))
    app.add_handler(CommandHandler("buy", cmd_buy))
    app.add_handler(CommandHandler("ath", cmd_ath))

    # Community commands
    app.add_handler(CommandHandler("praise", cmd_praise))
    app.add_handler(CommandHandler("kek", cmd_kek))
    app.add_handler(CommandHandler("moonmath", cmd_moonmath))
    app.add_handler(CommandHandler("hodlcheck", cmd_hodlcheck))
    app.add_handler(CommandHandler("links", cmd_links))
    app.add_handler(CommandHandler("prophecy", cmd_prophecy))
    app.add_handler(CommandHandler("ritual", cmd_ritual))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("h", cmd_help))
    app.add_handler(CommandHandler("praiseboard", cmd_praiseboard))
    app.add_handler(CommandHandler("join", cmd_join))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("lore", cmd_lore))
    app.add_handler(CommandHandler("initiate", cmd_initiate))
    app.add_handler(CommandHandler("relic", cmd_relic))
    app.add_handler(CommandHandler("fud", cmd_fud))
    app.add_handler(CommandHandler("whale", cmd_whale))
    app.add_handler(CommandHandler("voice", cmd_voice))
    app.add_handler(CommandHandler("canon", cmd_canon))

    # Admin commands
    app.add_handler(CommandHandler("setwhale", cmd_setwhale))
    app.add_handler(CommandHandler("addfud", cmd_addfud))
    app.add_handler(CommandHandler("removefud", cmd_removefud))
    app.add_handler(CommandHandler("listfud", cmd_listfud))
    app.add_handler(CommandHandler("announce", cmd_announce))
    app.add_handler(CommandHandler("warn", cmd_warn))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("setstrike", cmd_setstrike))

    # Anti-FUD (only in groups, non-commands)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        antifud_handler
    ))

    # Welcome new members
    app.add_handler(ChatMemberHandler(welcome_handler, ChatMemberHandler.CHAT_MEMBER))

    # Background jobs
    job_queue = app.job_queue
    job_queue.run_repeating(check_whale_alerts, interval=30, first=10)
    job_queue.run_repeating(check_price_alerts, interval=60, first=15)
    digest_hour = int(os.environ.get("DIGEST_HOUR_UTC", str(DEFAULT_DIGEST_HOUR_UTC)))
    job_queue.run_daily(send_daily_digest, time=time(hour=digest_hour, tzinfo=timezone.utc))

    logging.info("𓂀 Kekcoin bot is running. Praise Kek. 𓂀")
    app.run_polling(allowed_updates=["message", "chat_member"])


if __name__ == "__main__":
    main()
