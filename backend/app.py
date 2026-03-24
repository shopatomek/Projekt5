from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta
from typing import Any, Tuple, List

from database import execute_query
from analytics import calculate_crypto_kpis, calculate_stock_kpis
from ai_insights import generate_daily_summary, analyze_trend
from scheduler import run_scheduler
from data_quality import (
    run_data_quality_checks,
)  # Importuj funkcję do sprawdzania jakości danych


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
_summary_cache: dict[str, Any] = {"data": None, "cached_at": None}
SUMMARY_CACHE_TTL = timedelta(hours=2)

_trend_cache: dict[str, Tuple[Any, datetime]] = {}
TREND_CACHE_TTL = timedelta(minutes=30)


@app.on_event("startup")
async def startup_event():
    crypto_data = {
        "symbol": "BTC",
        "price_usd": 50000,
        "volume_24h": 1000000,
        "price_change_24h": 2.5,
    }
    weather_data = {
        "city": "Warsaw",
        "temperature": 20.5,
        "humidity": 60,
        "weather_condition": "sunny",
    }
    news_data = {
        "title": "Bitcoin Price Surges",
        "description": "Bitcoin price has surged by 10% in the last 24 hours.",
        "source": "BBC Business",
        "url": "https://www.bbc.com/news/business-12345678",
        "published_at": "2026-03-24T12:00:00Z",
    }
    run_data_quality_checks("crypto_prices", crypto_data)
    run_data_quality_checks("weather_data", weather_data)
    run_data_quality_checks("news_articles", news_data)


@app.get("/")
async def root():
    return {
        "status": "AI Dashboard API running",
        "version": "1.0.0",
        "source": "Binance API",
    }


def safe_list_concat(*lists: List[Any] | None) -> List[Any]:
    """Bezpiecznie łączy listy, obsługując None."""
    result = []
    for lst in lists:
        if lst is not None:
            result.extend(lst if isinstance(lst, list) else [lst])
    return result


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

        # Pobierz rzeczywiste dane z bazy do walidacji
        crypto_data = execute_query(
            "SELECT symbol, price_usd, volume_24h, price_change_24h FROM crypto_prices ORDER BY timestamp DESC LIMIT 1"
        )
        weather_data = execute_query(
            "SELECT city, temperature, humidity, weather_condition FROM weather_data ORDER BY timestamp DESC LIMIT 1"
        )
        news_data = execute_query(
            "SELECT title, description, source, url, published_at FROM news_articles ORDER BY published_at DESC LIMIT 1"
        )

        # Sprawdź jakość danych z rzeczywistych rekordów
        crypto_issues: List[str] = []
        if crypto_data:
            crypto_row = crypto_data[0]
            crypto_issues = (
                run_data_quality_checks(
                    "crypto_prices",
                    {
                        "symbol": crypto_row["symbol"],
                        "price_usd": crypto_row["price_usd"],
                        "volume_24h": crypto_row["volume_24h"],
                        "price_change_24h": crypto_row["price_change_24h"],
                    },
                )
                or []
            )
            print(f"[DEBUG] Crypto issues detected: {crypto_issues}")

        weather_issues: List[str] = []
        if weather_data:
            weather_row = weather_data[0]
            weather_issues = (
                run_data_quality_checks(
                    "weather_data",
                    {
                        "city": weather_row["city"],
                        "temperature": weather_row["temperature"],
                        "humidity": weather_row["humidity"],
                        "weather_condition": weather_row["weather_condition"],
                    },
                )
                or []
            )
            print(f"[DEBUG] Weather issues detected: {weather_issues}")

        news_issues: List[str] = []
        if news_data:
            news_row = news_data[0]
            news_issues = (
                run_data_quality_checks(
                    "news_articles",
                    {
                        "title": news_row["title"],
                        "description": news_row["description"],
                        "source": news_row["source"],
                        "url": news_row["url"],
                        "published_at": news_row["published_at"],
                    },
                )
                or []
            )
            print(f"[DEBUG] News issues detected: {news_issues}")

        # Połączenie wszystkich błędów w jedną listę (bezpieczne)
        all_issues = safe_list_concat(crypto_issues, weather_issues, news_issues)

        return {
            "crypto": crypto_kpis,
            "stocks": stock_kpis,
            "news": news,
            "weather": weather[0] if weather else None,
            "timestamp": str(datetime.now()),
            "data_quality_issues": all_issues,  # Puste, jeśli nie ma błędów
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/daily-summary")
async def get_ai_daily_summary():
    try:
        if (
            _summary_cache["data"] is not None
            and _summary_cache["cached_at"] is not None
        ):
            if datetime.now() - _summary_cache["cached_at"] < SUMMARY_CACHE_TTL:
                return _summary_cache["data"]

        weather_data = execute_query(
            "SELECT temperature, humidity FROM weather_data ORDER BY timestamp DESC LIMIT 1"
        )
        news_count_data = execute_query(
            "SELECT COUNT(*) as count FROM news_articles WHERE DATE(published_at) = CURRENT_DATE"
        )
        metrics = {
            "crypto_data": calculate_crypto_kpis().get("prices", []),
            "stock_data": calculate_stock_kpis().get("daily_changes", []),
            "news_count": news_count_data[0]["count"] if news_count_data else 0,
            "weather": weather_data[0] if weather_data else {},
        }

        summary = generate_daily_summary(metrics)

        _summary_cache["data"] = summary
        _summary_cache["cached_at"] = datetime.now()

        # Sprawdź jakość danych z rzeczywistych rekordów
        weather_data = execute_query(
            "SELECT city, temperature, humidity, weather_condition FROM weather_data ORDER BY timestamp DESC LIMIT 1"
        )
        news_data = execute_query(
            "SELECT title, description, source, url, published_at FROM news_articles ORDER BY published_at DESC LIMIT 1"
        )

        weather_issues: List[str] = []
        if weather_data:
            weather_row = weather_data[0]
            weather_issues = (
                run_data_quality_checks(
                    "weather_data",
                    {
                        "city": weather_row["city"],
                        "temperature": weather_row["temperature"],
                        "humidity": weather_row["humidity"],
                        "weather_condition": weather_row["weather_condition"],
                    },
                )
                or []
            )
            print(f"[DEBUG] Weather issues detected: {weather_issues}")

        news_issues: List[str] = []
        if news_data:
            news_row = news_data[0]
            news_issues = (
                run_data_quality_checks(
                    "news_articles",
                    {
                        "title": news_row["title"],
                        "description": news_row["description"],
                        "source": news_row["source"],
                        "url": news_row["url"],
                        "published_at": news_row["published_at"],
                    },
                )
                or []
            )
            print(f"[DEBUG] News issues detected: {news_issues}")

        all_issues = safe_list_concat(weather_issues, news_issues)

        return {
            **summary,
            "data_quality_issues": all_issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/crypto-trend")
async def get_crypto_trend(symbol: str = "BTC", days: int = 7):
    try:
        sym = symbol.upper()

        if sym in _trend_cache:
            cached_result, cached_at = _trend_cache[sym]
            if datetime.now() - cached_at < TREND_CACHE_TTL:
                return cached_result

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

        _trend_cache[sym] = (result, datetime.now())

        # Sprawdź jakość danych z rzeczywistych rekordów
        crypto_data = execute_query(
            "SELECT symbol, price_usd, volume_24h, price_change_24h FROM crypto_prices WHERE symbol = :symbol ORDER BY timestamp DESC LIMIT 1",
            {"symbol": sym},
        )
        crypto_issues: List[str] = []
        if crypto_data:
            crypto_row = crypto_data[0]
            crypto_issues = (
                run_data_quality_checks(
                    "crypto_prices",
                    {
                        "symbol": crypto_row["symbol"],
                        "price_usd": crypto_row["price_usd"],
                        "volume_24h": crypto_row["volume_24h"],
                        "price_change_24h": crypto_row["price_change_24h"],
                    },
                )
                or []
            )
            print(f"[DEBUG] Crypto issues detected: {crypto_issues}")

        return {
            **result,
            "data_quality_issues": crypto_issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
