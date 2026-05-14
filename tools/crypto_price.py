TOOL_NAME = "crypto_price"
TOOL_DESCRIPTION = "Get current cryptocurrency prices from CoinGecko. Supports BTC, ETH, SOL, DOGE, ADA, XRP and many more. Use when the user asks about crypto prices."

TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "symbol": {
            "type": "string",
            "description": "The cryptocurrency symbol (e.g. BTC, ETH, SOL, DOGE). Case-insensitive."
        },
        "vs_currency": {
            "type": "string",
            "description": "The fiat currency to compare against. Default: usd"
        }
    },
    "required": ["symbol"]
}

SYMBOL_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "DOGE": "dogecoin", "ADA": "cardano", "XRP": "ripple",
    "DOT": "polkadot", "AVAX": "avalanche-2", "LINK": "chainlink",
    "UNI": "uniswap", "SHIB": "shiba-inu", "LTC": "litecoin",
    "BCH": "bitcoin-cash", "ATOM": "cosmos", "NEAR": "near",
    "PEPE": "pepe", "SUI": "sui", "OP": "optimism",
    "ARB": "arbitrum", "APT": "aptos", "INJ": "injective-protocol",
    "SEI": "sei-network", "TIA": "celestia", "WIF": "dogwifcoin",
}


async def run(symbol: str, vs_currency: str = "usd") -> str:
    import httpx

    symbol = symbol.upper().strip()
    vs_currency = vs_currency.lower().strip()
    coin_id = SYMBOL_MAP.get(symbol, symbol.lower())

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                },
            )
            if resp.status_code == 429:
                return "CoinGecko rate limit reached. Please wait 60 seconds."
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return f"Error fetching price: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

    if coin_id not in data or not data[coin_id]:
        return f"Could not find price for '{symbol}'. Check the symbol or try the full CoinGecko coin ID (e.g., 'bitcoin')."

    info = data[coin_id]
    price = info.get(vs_currency)
    if price is None:
        return f"No {vs_currency.upper()} price available for {symbol}."

    change_24h = info.get(f"{vs_currency}_24h_change")

    if price >= 1:
        msg = f"{symbol} = ${price:,.2f}"
    elif price >= 0.01:
        msg = f"{symbol} = ${price:.4f}"
    else:
        msg = f"{symbol} = ${price:.8f}"

    if change_24h is not None:
        direction = "+" if change_24h >= 0 else ""
        msg += f" (24h: {direction}{change_24h:.2f}%)"

    return msg
