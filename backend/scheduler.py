# backend/scheduler.py

import asyncio
import httpx
from datetime import datetime
from database import execute_query
from data_quality import (
    run_data_quality_checks,
)  # Importuj funkcję do sprawdzania jakości danych

BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"

symbols_str = '["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","TRXUSDT","DOTUSDT","LINKUSDT","MATICUSDT","LTCUSDT","UNIUSDT","ATOMUSDT","NEARUSDT","XLMUSDT","ETCUSDT","FILUSDT","APTUSDT"]'


async def fetch_and_store_crypto():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            req = httpx.Request("GET", BINANCE_URL, params={"symbols": symbols_str})
            resp = await client.send(req)
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
            VALUES {",".join(rows)}
            ON CONFLICT DO NOTHING
        """
        )
        execute_query(
            "DELETE FROM crypto_prices WHERE timestamp < NOW() - INTERVAL '30 days'"
        )

        # Wywołaj funkcję do sprawdzania jakości danych
        for row in rows:
            symbol, price_usd, _, volume_24h, price_change_24h = row[1:-1].split(",")
            price_usd = float(price_usd)
            volume_24h = int(volume_24h)
            price_change_24h = float(price_change_24h)
            run_data_quality_checks(
                "crypto_prices",
                {
                    "symbol": symbol.strip()[1:-1],
                    "price_usd": price_usd,
                    "volume_24h": volume_24h,
                    "price_change_24h": price_change_24h,
                },
            )

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Binance: zapisano {len(rows)} rekordów"
        )
        return {"status": "ok", "count": len(rows)}
    except Exception as e:
        print(f"Błąd fetch_and_store_crypto: {e}")
        return {"status": "error", "message": str(e)}


async def run_scheduler():
    while True:
        await fetch_and_store_crypto()
        await asyncio.sleep(300)
