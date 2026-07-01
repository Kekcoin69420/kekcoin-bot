import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_CHAT_ID = int(os.environ["GROUP_CHAT_ID"])
ADMIN_IDS = [int(x) for x in os.environ["ADMIN_IDS"].split(",")]
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "")
DB_PATH = os.environ.get("DB_PATH", "./data/kek.db")

CA = "BY4ttYDiMWsyBebNNjNoSfA3krvZvUaPaaYdJsWmpump"
PAIR = "CBW8oZUhbjSbMigGihC5Lh5g7NQEGxVTZ1ikVjH1HBt9"
TOTAL_SUPPLY = 973_806_242

DEXSCREENER_URL = f"https://api.dexscreener.com/latest/dex/pairs/solana/{PAIR}"
HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
HELIUS_ACCOUNTS_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

JUPITER_URL = f"https://jup.ag/swap/SOL-{CA}"
PUMPFUN_URL = f"https://pump.fun/coin/{CA}"
DEXSCREENER_CHART_URL = f"https://dexscreener.com/solana/{PAIR}"

WEBSITE_URL = "https://www.kektemple.com/"
TWITTER_URL = "https://x.com/kekcoin69420"
TELEGRAM_URL = "https://t.me/kekcoincto_tg"

DEFAULT_WHALE_THRESHOLD = 500.0
DEFAULT_HOLDER_MILESTONES = [1000, 5000, 10000, 25000, 50000, 100000]
DEFAULT_STRIKE_THRESHOLD = 3
DEFAULT_VOLUME_SPIKE_MULTIPLE = 2.0
DEFAULT_VOLUME_LOOKBACK_DAYS = 7
DEFAULT_DIGEST_HOUR_UTC = 9

DEFAULT_FUD_KEYWORDS = [
    "rug", "rugpull", "scam", "dead", "honeypot",
    "dev ran", "abandoned", "exit scam", "sell now", "worthless"
]

# Supabase (praise board + /define lexicon)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vyrxqrqfznbpxyzhpmyw.supabase.co")
SUPABASE_ANON_KEY = os.environ.get(
    "SUPABASE_ANON_KEY",
    "sb_publishable_dCr2XwJ6ZVP2UYuXwYKmzQ_qcJiBOft",
)
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
