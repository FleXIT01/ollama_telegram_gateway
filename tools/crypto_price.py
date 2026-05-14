TOOL_NAME = "crypto_price"
TOOL_DESCRIPTION = "Get current cryptocurrency prices from Binance public API. Supports BTC, ETH, SOL, and many more. Use when the user asks about crypto prices or wants to check the market."

TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "symbol": {
            "type": "string",
            "description": "The cryptocurrency symbol (e.g. BTC, ETH, SOL, DOGE, ADA). Case-insensitive."
        },
        "vs_currency": {
            "type": "string",
            "description": "The fiat currency to compare against. Default: usd"
        }
    },
    "required": ["symbol"]
}


async def run(symbol: str, vs_currency: str = "usd") -> str:
    import httpx

    symbol = symbol.upper().strip()
    vs_currency = vs_currency.lower().strip()

    symbol_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "DOGE": "dogecoin",
        "ADA": "cardano",
        "XRP": "ripple",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "SHIB": "shiba-inu",
        "LTC": "litecoin",
        "BCH": "bitcoin-cash",
        "ATOM": "cosmos",
        "NEAR": "near",
        "PEPE": "pepe",
    }

    coin_id = symbol_map.get(symbol, symbol.lower())

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": vs_currency,
                "include_24hr_change": "true",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if coin_id not in data:
        return f"Could not find price for {symbol}. Try using the full CoinGecko ID."

    info = data[coin_id]
    price = info.get(vs_currency, "N/A")
    change_24h = info.get(f"{vs_currency}_24h_change", None)

    msg = f"{symbol} = ${price:,.4f}" if isinstance(price, (int, float)) else f"{symbol} = {price}"
    if isinstance(change_24h, (int, float)):
        direction = "+" if change_24h >= 0 else ""
        msg += f" (24h: {direction}{change_24h:.2f}%)"

    return msg
