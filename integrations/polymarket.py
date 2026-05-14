from __future__ import annotations

import httpx

CLOB_BASE = "https://clob.polymarket.com"
GAMMA_BASE = "https://gamma-api.polymarket.com"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://polymarket.com/",
}


def _get(url: str, params: dict = None) -> dict | list:
    with httpx.Client(timeout=15, headers=_HEADERS) as client:
        r = client.get(url, params=params or {})
        r.raise_for_status()
        return r.json()


def search_markets(query: str = "", limit: int = 20, active: bool = True) -> list[dict]:
    params: dict = {"limit": limit}
    if query:
        params["_q"] = query
    if active:
        params["active"] = "true"
        params["closed"] = "false"
    data = _get(f"{GAMMA_BASE}/markets", params)
    markets = data if isinstance(data, list) else data.get("markets", [])
    return [_fmt_gamma(m) for m in markets[:limit]]


def get_market(condition_id: str) -> dict:
    try:
        data = _get(f"{CLOB_BASE}/markets/{condition_id}")
        return _fmt_clob(data)
    except Exception:
        data = _get(f"{GAMMA_BASE}/markets", {"conditionId": condition_id})
        items = data if isinstance(data, list) else data.get("markets", [data])
        return _fmt_gamma(items[0]) if items else {"error": "Market not found"}


def get_trending_markets(limit: int = 10) -> list[dict]:
    data = _get(f"{GAMMA_BASE}/markets", {
        "active": "true", "closed": "false",
        "_sort": "volume24hr", "_order": "DESC", "limit": limit
    })
    markets = data if isinstance(data, list) else data.get("markets", [])
    return [_fmt_gamma(m) for m in markets[:limit]]


def get_market_orderbook(token_id: str) -> dict:
    data = _get(f"{CLOB_BASE}/book", {"token_id": token_id})
    bids = data.get("bids", [])[:5]
    asks = data.get("asks", [])[:5]
    return {
        "token_id": token_id,
        "best_bid": bids[0]["price"] if bids else None,
        "best_ask": asks[0]["price"] if asks else None,
        "top_bids": bids,
        "top_asks": asks,
    }


def get_market_price_history(condition_id: str, interval: str = "1d") -> list[dict]:
    try:
        data = _get(f"{CLOB_BASE}/prices-history", {
            "market": condition_id,
            "interval": interval,
            "fidelity": 60,
        })
        return data.get("history", [])
    except Exception as e:
        return [{"error": str(e)}]


def _fmt_gamma(m: dict) -> dict:
    return {
        "id": m.get("conditionId", m.get("id", "")),
        "slug": m.get("slug", ""),
        "question": m.get("question", m.get("title", "")),
        "description": m.get("description", "")[:300],
        "yes_price": m.get("outcomePrices", ["?"])[0] if m.get("outcomePrices") else m.get("bestBid"),
        "no_price": m.get("outcomePrices", ["?", "?"])[1] if m.get("outcomePrices") and len(m.get("outcomePrices", [])) > 1 else None,
        "volume": m.get("volume", 0),
        "volume_24hr": m.get("volume24hr", 0),
        "liquidity": m.get("liquidity", 0),
        "end_date": m.get("endDate", m.get("endDateIso", "")),
        "active": m.get("active", True),
        "closed": m.get("closed", False),
        "tags": [t.get("label", t) if isinstance(t, dict) else t for t in m.get("tags", [])],
        "url": f"https://polymarket.com/event/{m.get('slug', '')}",
    }


def _fmt_clob(m: dict) -> dict:
    tokens = m.get("tokens", [])
    yes_token = next((t for t in tokens if t.get("outcome") == "Yes"), tokens[0] if tokens else {})
    no_token = next((t for t in tokens if t.get("outcome") == "No"), tokens[1] if len(tokens) > 1 else {})
    return {
        "id": m.get("condition_id", ""),
        "question": m.get("question", ""),
        "description": m.get("description", "")[:300],
        "yes_price": yes_token.get("price"),
        "no_price": no_token.get("price"),
        "volume": m.get("volume", 0),
        "liquidity": m.get("liquidity", 0),
        "end_date": m.get("end_date_iso", ""),
        "active": m.get("active", True),
        "closed": m.get("closed", False),
        "url": f"https://polymarket.com/event/{m.get('market_slug', '')}",
    }
