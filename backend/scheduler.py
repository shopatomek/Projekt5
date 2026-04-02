
# ZMIANA WZGLĘDEM ORYGINAŁU:
# Stara wersja: importuje run_data_quality_checks() z data_quality.py (plik-funkcja)
# Nowa wersja:  importuje engine z data_quality/ (pakiet-moduł ABC)
#
# RÓŻNICA W ZACHOWANIU:
# Stara: run_data_quality_checks() → tylko print() do stdout, nic w bazie
# Nowa:  engine.run() → LogReporter (stdout) + DatabaseReporter (ai_insights w bazie)
#
# PRZEPŁYW:
# 1. Pobieramy dane z Binance (bez zmian)
# 2. Budujemy bulk INSERT (bez zmian)
# 3. Zapisujemy do crypto_prices (bez zmian)
# 4. Dla każdego rekordu wywołujemy engine.run() — NOWE
# 5. Jeśli jest błąd DQ → LogReporter wypisuje do stdout
#                        → DatabaseReporter zapisuje do ai_insights
# 6. Czyścimy stare dane (bez zmian)

import asyncio
import httpx
from datetime import datetime
from database import execute_query
from data_quality.engine import engine

BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"

symbols_str = '["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","TRXUSDT","DOTUSDT","LINKUSDT","MATICUSDT","LTCUSDT","UNIUSDT","ATOMUSDT","NEARUSDT","XLMUSDT","ETCUSDT","FILUSDT","APTUSDT"]'


async def fetch_and_store_crypto():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            req = httpx.Request("GET", BINANCE_URL, params={"symbols": symbols_str})
            resp = await client.send(req)
            resp.raise_for_status()
            tickers = resp.json()

        # Budujemy listę dict zamiast parsowania string SQL (bezpieczniejsze)
        records = []
        for t in tickers:
            records.append({
                "symbol": t["symbol"].replace("USDT", ""),
                "price_usd": float(t.get("lastPrice") or 0),
                "market_cap": 0,
                "volume_24h": int(float(t.get("quoteVolume") or 0)),
                "price_change_24h": float(t.get("priceChangePercent") or 0),
            })

        # ── KROK 1: Data Quality check PRZED zapisem ─────────────────────────
        # Sprawdzamy każdy rekord. engine.run() zwraca (report, clean_record).
        # clean_record to naprawiony rekord (lub oryginalny jeśli naprawa niemożliwa).
        # Jeśli jest błąd → DatabaseReporter zapisze go do ai_insights automatycznie.

        clean_records = []
        dq_failures = 0

        for record in records:
            report, clean = engine.run(
                "crypto_prices",
                record,
                record_id=record["symbol"]
            )
            if not report.passed:
                dq_failures += 1
            clean_records.append(clean)

        # ── KROK 2: Bulk INSERT do crypto_prices ─────────────────────────────
        # Używamy clean_records (po naprawie) a nie oryginalnych records
        sql_values = ", ".join([
            f"('{r['symbol']}', {r['price_usd']:.8f}, {r['market_cap']}, "
            f"{r['volume_24h']}, {r['price_change_24h']:.4f})"
            for r in clean_records
        ])

        execute_query(
            f"""
            INSERT INTO crypto_prices (symbol, price_usd, market_cap, volume_24h, price_change_24h)
            VALUES {sql_values}
            ON CONFLICT DO NOTHING
            """
        )

        # ── KROK 3: Cleanup starych danych ───────────────────────────────────
        execute_query(
            "DELETE FROM crypto_prices WHERE timestamp < NOW() - INTERVAL '30 days'"
        )
        try:
            execute_query(
                "REFRESH MATERIALIZED VIEW CONCURRENTLY mart_market_daily"
            )
        except Exception:
            pass  
        status_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Binance: {len(clean_records)} rekordów"
        if dq_failures:
            status_msg += f" | ⚠️ DQ failures: {dq_failures}"
        print(status_msg)

        return {"status": "ok", "count": len(clean_records), "dq_failures": dq_failures}

    except Exception as e:
        print(f"Błąd fetch_and_store_crypto: {e}")
        return {"status": "error", "message": str(e)}


async def run_scheduler():
    while True:
        await fetch_and_store_crypto()
        await asyncio.sleep(300)