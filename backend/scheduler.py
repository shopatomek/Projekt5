import os
import asyncio
import httpx
from datetime import datetime
from database import execute_query

BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"

SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "TRXUSDT",
    "DOTUSDT",
    "LINKUSDT",
    "MATICUSDT",
    "LTCUSDT",
    "UNIUSDT",
    "ATOMUSDT",
    "NEARUSDT",
    "XLMUSDT",
    "ETCUSDT",
    "FILUSDT",
    "APTUSDT",
]


async def fetch_and_store_crypto():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(BINANCE_URL, params={"symbols": str(SYMBOLS).replace("'", '"')})
            resp.raise_for_status()
            tickers = resp.json()

        rows = []
        for t in tickers:
            symbol = t["symbol"].replace("USDT", "")
            price = float(t.get("lastPrice") or 0)
            vol = int(float(t.get("quoteVolume") or 0))
            change = float(t.get("priceChangePercent") or 0)
            rows.append(f"('{symbol}', {price:.8f}, 0, {vol}, {change:.4f})")

        execute_query(
            f"""
            INSERT INTO crypto_prices (symbol, price_usd, market_cap, volume_24h, price_change_24h)
            VALUES {','.join(rows)}
            ON CONFLICT DO NOTHING
        """
        )
        execute_query("DELETE FROM crypto_prices WHERE timestamp < NOW() - INTERVAL '30 days'")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Binance: zapisano {len(rows)} rekordów")
        return {"status": "ok", "count": len(rows)}
    except Exception as e:
        print(f"Błąd fetch_and_store_crypto: {e}")
        return {"status": "error", "message": str(e)}


async def run_scheduler():
    while True:
        await fetch_and_store_crypto()
        await asyncio.sleep(300)
