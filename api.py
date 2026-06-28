import httpx
from config import DEXSCREENER_URL, HELIUS_RPC_URL, CA, PAIR

TIMEOUT = 10.0


async def get_pair_data() -> dict | None:
    """Fetch price, MC, volume, etc. from DexScreener. Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(DEXSCREENER_URL)
            resp.raise_for_status()
            data = resp.json()
        pairs = data.get("pairs") or []
        p = pairs[0] if pairs else data.get("pair")
        if not p:
            return None
        return {
            "price": float(p.get("priceUsd", 0)),
            "market_cap": float(p.get("marketCap") or p.get("fdv") or 0),
            "liquidity": float((p.get("liquidity") or {}).get("usd", 0)),
            "volume_24h": float((p.get("volume") or {}).get("h24", 0)),
            "change_24h": float((p.get("priceChange") or {}).get("h24", 0)),
            "txns_24h": int((p.get("txns") or {}).get("h24", {}).get("buys", 0))
                       + int((p.get("txns") or {}).get("h24", {}).get("sells", 0)),
        }
    except Exception:
        return None


async def get_recent_signatures(limit: int = 20) -> list[dict]:
    """Fetch recent tx signatures for the pair via Helius RPC. Returns [] on failure."""
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "getSignaturesForAddress",
        "params": [PAIR, {"limit": limit}]
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(HELIUS_RPC_URL, json=payload)
            resp.raise_for_status()
            return resp.json().get("result", [])
    except Exception:
        return []


async def get_transaction(signature: str) -> dict | None:
    """Fetch full transaction detail for a signature. Returns None on failure."""
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "getTransaction",
        "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(HELIUS_RPC_URL, json=payload)
            resp.raise_for_status()
            return resp.json().get("result")
    except Exception:
        return None


async def get_holder_count() -> int | None:
    """Get SPL token holder count via Helius token accounts endpoint."""
    from config import HELIUS_API_KEY
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            rpc_payload = {
                "jsonrpc": "2.0", "id": 1,
                "method": "getTokenAccounts",
                "params": {"mint": CA, "page": 1, "limit": 1}
            }
            resp = await client.post(url, json=rpc_payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {}).get("total")
    except Exception:
        return None


def parse_swap_usd(tx: dict, current_price: float) -> tuple[float, str] | None:
    """
    Parse a transaction to determine swap USD value and direction.
    Returns (usd_value, "buy" | "sell") or None if not a swap.
    Looks at pre/postTokenBalances for the KEK mint.
    """
    if not tx:
        return None
    meta = tx.get("meta", {})
    pre = meta.get("preTokenBalances", [])
    post = meta.get("postTokenBalances", [])

    pre_map = {b["accountIndex"]: float(b["uiTokenAmount"]["uiAmount"] or 0) for b in pre if b.get("mint") == CA}
    post_map = {b["accountIndex"]: float(b["uiTokenAmount"]["uiAmount"] or 0) for b in post if b.get("mint") == CA}

    all_indexes = set(pre_map) | set(post_map)
    total_delta = sum(post_map.get(i, 0) - pre_map.get(i, 0) for i in all_indexes)

    if abs(total_delta) < 1:
        return None

    usd_value = abs(total_delta) * current_price
    direction = "buy" if total_delta > 0 else "sell"
    return usd_value, direction
