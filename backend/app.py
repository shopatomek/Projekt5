from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple

from database import execute_query
from analytics import calculate_crypto_kpis, calculate_stock_kpis
from ai_insights import generate_daily_summary, analyze_trend
from scheduler import run_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_scheduler())
    yield
    task.cancel()


app = FastAPI(title="AI Business Intelligence Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cache configuration ───────────────────────────────────────────────────────
# Summary cache: reused for 2h — Groq calls are expensive token-wise
_summary_cache: dict[str, Any] = {"data": None, "cached_at": None}
SUMMARY_CACHE_TTL = timedelta(hours=2)

# Trend cache: per symbol, reused for 30min
_trend_cache: dict[str, Tuple[Any, datetime]] = {}
TREND_CACHE_TTL = timedelta(minutes=30)


@app.get("/")
async def root():
    return {"status": "AI Dashboard API running", "version": "1.0.0", "source": "Binance API"}


@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    try:
        crypto_kpis = calculate_crypto_kpis()
        stock_kpis = calculate_stock_kpis()
        news = execute_query(
            """
            SELECT title, description, source, published_at
            FROM news_articles ORDER BY published_at DESC LIMIT 10
        """
        )
        weather = execute_query(
            """
            SELECT city, temperature, humidity, weather_condition
            FROM weather_data ORDER BY timestamp DESC LIMIT 1
        """
        )
        return {"crypto": crypto_kpis, "stocks": stock_kpis, "news": news, "weather": weather[0] if weather else None, "timestamp": str(datetime.now())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/daily-summary")
async def get_ai_daily_summary():
    try:
        # Return from cache if still fresh
        if _summary_cache["data"] is not None and _summary_cache["cached_at"] is not None:
            if datetime.now() - _summary_cache["cached_at"] < SUMMARY_CACHE_TTL:
                return _summary_cache["data"]

        # Cache miss — fetch fresh data and call Groq
        weather_data = execute_query("SELECT temperature, humidity FROM weather_data ORDER BY timestamp DESC LIMIT 1")
        news_count_data = execute_query("SELECT COUNT(*) as count FROM news_articles WHERE DATE(published_at) = CURRENT_DATE")
        metrics = {
            "crypto_data": calculate_crypto_kpis().get("prices", []),
            "stock_data": calculate_stock_kpis().get("daily_changes", []),
            "news_count": news_count_data[0]["count"] if news_count_data else 0,
            "weather": weather_data[0] if weather_data else {},
        }

        summary = generate_daily_summary(metrics)

        # Store in cache
        _summary_cache["data"] = summary
        _summary_cache["cached_at"] = datetime.now()

        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/crypto-trend")
async def get_crypto_trend(symbol: str = "BTC", days: int = 7):
    try:
        sym = symbol.upper()

        # Return from cache if still fresh
        if sym in _trend_cache:
            cached_result, cached_at = _trend_cache[sym]
            if datetime.now() - cached_at < TREND_CACHE_TTL:
                return cached_result

        # Cache miss — query DB and call Groq
        query = f"""
        SELECT price_usd as value, timestamp
        FROM crypto_prices
        WHERE symbol = :symbol
        AND timestamp >= NOW() - INTERVAL '{days} days'
        ORDER BY timestamp
        """
        data = execute_query(query, {"symbol": sym})
        trend_analysis = analyze_trend(data, f"{sym} price")

        result = {"symbol": symbol, "data": data, "ai_analysis": trend_analysis}

        # Store in cache
        _trend_cache[sym] = (result, datetime.now())

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
