from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta
from typing import Any, Tuple, List
from collections import Counter
import os
import httpx
from database import execute_query
from analytics import calculate_crypto_kpis, calculate_stock_kpis
from ai_insights import generate_daily_summary, analyze_trend, explain_anomaly
from scheduler import run_scheduler
from data_quality.engine import engine
from pydantic import BaseModel


# =============================================================================
# Modele Pydantic dla nowych endpointów
# =============================================================================


class AnomalyRequest(BaseModel):
    symbol: str
    price_usd: float
    price_change_24h: float
    detected_at: str = ""


# =============================================================================
# Lifespan i konfiguracja aplikacji
# =============================================================================
async def fetch_initial_news_and_weather():
    """Pobiera newsy i pogodę natychmiast po starcie backendu."""
    print("🌐 Pobieranie początkowych danych (newsy, pogoda)...")

    # 1. Newsy z BBC RSS
    try:
        async with httpx.AsyncClient() as client:
            rss_response = await client.get("https://feeds.bbci.co.uk/news/business/rss.xml")
            import xml.etree.ElementTree as ET

            root = ET.fromstring(rss_response.text)
            items = root.findall(".//item")
            count = 0
            for item in items[:10]:
                title_elem = item.find("title")
                title = title_elem.text if title_elem is not None else ""
                title = title.replace("'", "''") if title else ""

                desc_elem = item.find("description")
                description = desc_elem.text if desc_elem is not None else ""
                description = description.replace("'", "''")[:500] if description else ""

                link_elem = item.find("link")
                link = link_elem.text if link_elem is not None else ""

                pub_elem = item.find("pubDate")
                pub_date = pub_elem.text if pub_elem is not None else datetime.now().isoformat()

                execute_query(
                    """
                    INSERT INTO news_articles (title, description, source, url, published_at)
                    VALUES (%s, %s, 'BBC News', %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    {"title": title, "description": description, "url": link, "published_at": pub_date},
                )
                count += 1
            print(f"✅ Dodano {count} artykułów")
    except Exception as e:
        print(f"❌ Błąd pobierania newsów: {e}")

    # 2. Pogoda z Open-Meteo
    try:
        async with httpx.AsyncClient() as client:
            weather_response = await client.get(
                "https://api.open-meteo.com/v1/forecast", params={"latitude": 52.23, "longitude": 21.01, "current": "temperature_2m,relative_humidity_2m,weather_code", "timezone": "Europe/Warsaw"}
            )
            data = weather_response.json()
            current = data.get("current", {})
            temp = current.get("temperature_2m", 0)
            humidity = current.get("relative_humidity_2m", 0)
            weather_code = current.get("weather_code", 0)

            weather_map = {
                0: "clear sky",
                1: "mainly clear",
                2: "partly cloudy",
                3: "overcast",
                45: "foggy",
                51: "light drizzle",
                61: "light rain",
                63: "moderate rain",
                65: "heavy rain",
                71: "light snow",
                80: "rain showers",
                95: "thunderstorm",
            }
            condition = weather_map.get(weather_code, "unknown")

            execute_query(
                """
                INSERT INTO weather_data (city, temperature, humidity, weather_condition)
                VALUES ('Warsaw', %s, %s, %s)
                """,
                {"temperature": temp, "humidity": humidity, "weather_condition": condition},
            )
            print(f"✅ Dodano pogodę: {temp}°C, {condition}")
    except Exception as e:
        print(f"❌ Błąd pobierania pogody: {e}")

    # 3. Daily Summary (tylko jeśli są dane)
    try:
        news_cnt_result = execute_query("SELECT COUNT(*) as cnt FROM news_articles")
        news_cnt = news_cnt_result[0]["cnt"] if news_cnt_result else 0
        if news_cnt > 0:
            from ai_insights import generate_daily_summary
            from analytics import calculate_crypto_kpis

            weather_row = execute_query("SELECT temperature, humidity FROM weather_data ORDER BY timestamp DESC LIMIT 1")
            weather_data = weather_row[0] if weather_row else {}

            news_count_today_result = execute_query("SELECT COUNT(*) as count FROM news_articles WHERE DATE(published_at) = CURRENT_DATE")
            news_count_today = news_count_today_result[0]["count"] if news_count_today_result else 0

            metrics = {
                "crypto_data": calculate_crypto_kpis().get("prices", []),
                "stock_data": [],
                "news_count": news_count_today,
                "weather": weather_data,
            }
            summary = generate_daily_summary(metrics)
            execute_query(
                """
                INSERT INTO ai_insights (insight_type, content, generated_at)
                VALUES ('daily_summary', %s, NOW())
                """,
                {"content": summary},
            )
            print("✅ Wygenerowano Daily Summary")
    except Exception as e:
        print(f"❌ Błąd generowania Daily Summary: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start: pobieranie początkowych danych (nie blokuje)
    asyncio.create_task(fetch_initial_news_and_weather())
    # Uruchom scheduler w tle
    task = asyncio.create_task(run_scheduler())
    yield
    # Shutdown: anuluj zadania
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


# =============================================================================
# Endpoint główny
# =============================================================================


@app.get("/")
async def root():
    return {
        "status": "AI Dashboard API running",
        "version": "1.0.0",
        "source": "Binance API",
    }


# =============================================================================
# Pomocnicza funkcja do łączenia list
# =============================================================================


def safe_list_concat(*lists: List[Any] | None) -> List[Any]:
    """Bezpiecznie łączy listy, obsługując None."""
    result = []
    for lst in lists:
        if lst is not None:
            result.extend(lst if isinstance(lst, list) else [lst])
    return result


# =============================================================================
# Endpoint /api/dashboard/overview (poprawiony – używa engine.run)
# =============================================================================


@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    try:
        crypto_kpis = calculate_crypto_kpis()
        stock_kpis = calculate_stock_kpis()
        news = execute_query(
            """
            SELECT title, description, source, published_at, url
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
        crypto_data = execute_query("SELECT symbol, price_usd, volume_24h, price_change_24h FROM crypto_prices ORDER BY timestamp DESC LIMIT 1")
        weather_data = execute_query("SELECT city, temperature, humidity, weather_condition FROM weather_data ORDER BY timestamp DESC LIMIT 1")
        news_data = execute_query("SELECT title, description, source, url, published_at FROM news_articles ORDER BY published_at DESC LIMIT 1")

        # Sprawdź jakość danych z rzeczywistych rekordów używając nowego silnika
        crypto_issues: List[str] = []
        if crypto_data:
            crypto_row = crypto_data[0]
            report, _ = engine.run(
                "crypto_prices",
                {
                    "symbol": crypto_row["symbol"],
                    "price_usd": crypto_row["price_usd"],
                    "volume_24h": crypto_row["volume_24h"],
                    "price_change_24h": crypto_row["price_change_24h"],
                },
                record_id=crypto_row["symbol"],
            )
            crypto_issues = report.failed_checks
            print(f"[DEBUG] Crypto issues detected: {crypto_issues}")

        weather_issues: List[str] = []
        if weather_data:
            weather_row = weather_data[0]
            report, _ = engine.run(
                "weather_data",
                {
                    "city": weather_row["city"],
                    "temperature": weather_row["temperature"],
                    "humidity": weather_row["humidity"],
                    "weather_condition": weather_row["weather_condition"],
                },
                record_id=weather_row["city"],
            )
            weather_issues = report.failed_checks
            print(f"[DEBUG] Weather issues detected: {weather_issues}")

        news_issues: List[str] = []
        if news_data:
            news_row = news_data[0]
            report, _ = engine.run(
                "news_articles",
                {
                    "title": news_row["title"],
                    "description": news_row["description"],
                    "source": news_row["source"],
                    "url": news_row["url"],
                    "published_at": news_row["published_at"],
                },
                record_id=news_row.get("title", "unknown")[:50],
            )
            news_issues = report.failed_checks
            print(f"[DEBUG] News issues detected: {news_issues}")

        all_issues = safe_list_concat(crypto_issues, weather_issues, news_issues)

        return {
            "crypto": crypto_kpis,
            "stocks": stock_kpis,
            "news": news,
            "weather": weather[0] if weather else None,
            "timestamp": str(datetime.now()),
            "data_quality_issues": all_issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Endpoint /api/ai/daily-summary (poprawiony – używa engine.run)
# =============================================================================


@app.get("/api/ai/daily-summary")
async def get_ai_daily_summary():
    try:
        if _summary_cache["data"] is not None and _summary_cache["cached_at"] is not None:
            if datetime.now() - _summary_cache["cached_at"] < SUMMARY_CACHE_TTL:
                return _summary_cache["data"]

        weather_data = execute_query("SELECT temperature, humidity FROM weather_data ORDER BY timestamp DESC LIMIT 1")
        news_count_data = execute_query("SELECT COUNT(*) as count FROM news_articles WHERE DATE(published_at) = CURRENT_DATE")
        metrics = {
            "crypto_data": calculate_crypto_kpis().get("prices", []),
            "stock_data": calculate_stock_kpis().get("daily_changes", []),
            "news_count": news_count_data[0]["count"] if news_count_data else 0,
            "weather": weather_data[0] if weather_data else {},
        }

        summary = generate_daily_summary(metrics)

        _summary_cache["data"] = summary
        _summary_cache["cached_at"] = datetime.now()

        # Sprawdź jakość danych z rzeczywistych rekordów używając nowego silnika
        weather_data_full = execute_query("SELECT city, temperature, humidity, weather_condition FROM weather_data ORDER BY timestamp DESC LIMIT 1")
        news_data = execute_query("SELECT title, description, source, url, published_at FROM news_articles ORDER BY published_at DESC LIMIT 1")

        weather_issues: List[str] = []
        if weather_data_full:
            weather_row = weather_data_full[0]
            report, _ = engine.run(
                "weather_data",
                {
                    "city": weather_row["city"],
                    "temperature": weather_row["temperature"],
                    "humidity": weather_row["humidity"],
                    "weather_condition": weather_row["weather_condition"],
                },
                record_id=weather_row["city"],
            )
            weather_issues = report.failed_checks
            print(f"[DEBUG] Weather issues detected: {weather_issues}")

        news_issues: List[str] = []
        if news_data:
            news_row = news_data[0]
            report, _ = engine.run(
                "news_articles",
                {
                    "title": news_row["title"],
                    "description": news_row["description"],
                    "source": news_row["source"],
                    "url": news_row["url"],
                    "published_at": news_row["published_at"],
                },
                record_id=news_row.get("title", "unknown")[:50],
            )
            news_issues = report.failed_checks
            print(f"[DEBUG] News issues detected: {news_issues}")

        all_issues = safe_list_concat(weather_issues, news_issues)

        return {
            **summary,
            "data_quality_issues": all_issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Endpoint /api/charts/crypto-trend (poprawiony – używa engine.run)
# =============================================================================


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
        data = execute_query(query, {"symbol": sym}) or []
        trend_analysis = analyze_trend(data, f"{sym} price")

        result = {"symbol": symbol, "data": data, "ai_analysis": trend_analysis}

        _trend_cache[sym] = (result, datetime.now())

        # Sprawdź jakość danych z rzeczywistych rekordów używając nowego silnika
        crypto_data = execute_query(
            "SELECT symbol, price_usd, volume_24h, price_change_24h FROM crypto_prices WHERE symbol = :symbol ORDER BY timestamp DESC LIMIT 1",
            {"symbol": sym},
        )
        crypto_issues: List[str] = []
        if crypto_data:
            crypto_row = crypto_data[0]
            report, _ = engine.run(
                "crypto_prices",
                {
                    "symbol": crypto_row["symbol"],
                    "price_usd": crypto_row["price_usd"],
                    "volume_24h": crypto_row["volume_24h"],
                    "price_change_24h": crypto_row["price_change_24h"],
                },
                record_id=crypto_row["symbol"],
            )
            crypto_issues = report.failed_checks
            print(f"[DEBUG] Crypto issues detected: {crypto_issues}")

        return {
            **result,
            "data_quality_issues": crypto_issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NOWE ENDPOINTY (z app_new_endpoints.py)
# =============================================================================


@app.post("/api/ai/explain-anomaly")
async def get_anomaly_explanation(req: AnomalyRequest):
    """
    Wywoływany przez n8n WF3B po wykryciu anomalii cenowej.
    Zwraca wyjaśnienie anomalii wygenerowane przez Groq.
    """
    explanation = explain_anomaly(
        {
            "symbol": req.symbol,
            "price_usd": req.price_usd,
            "price_change_24h": req.price_change_24h,
            "detected_at": req.detected_at,
        }
    )
    return {"explanation": explanation}


@app.get("/api/dq/report")
async def get_dq_report(hours: int = 24):
    """
    Raport Data Quality z ostatnich N godzin.
    Używany przez Metabase i frontend do pokazania stanu jakości danych.
    """
    failures = (
        execute_query(
            f"""
        SELECT
            content->>'table' as table_name,
            content->>'record_id' as record_id,
            content->'failed_checks' as failed_checks,
            content->>'auto_repaired' as auto_repaired,
            generated_at
        FROM ai_insights
        WHERE insight_type = 'dq_failure'
          AND generated_at >= NOW() - INTERVAL '{hours} hours'
        ORDER BY generated_at DESC
        LIMIT 100
        """
        )
        or []
    )

    anomalies = (
        execute_query(
            f"""
        SELECT
            content->>'message' as message,
            content->'affected_symbols' as symbols,
            generated_at
        FROM ai_insights
        WHERE insight_type = 'price_anomaly'
          AND generated_at >= NOW() - INTERVAL '{hours} hours'
        ORDER BY generated_at DESC
        LIMIT 20
        """
        )
        or []
    )

    by_table = {}
    failure_types = []
    for f in failures:
        tbl = f.get("table_name", "unknown")
        by_table[tbl] = by_table.get(tbl, 0) + 1
        checks = f.get("failed_checks")
        if isinstance(checks, list):
            failure_types.extend(checks)

    most_common = Counter(failure_types).most_common(1)[0][0] if failure_types else None

    return {
        "period_hours": hours,
        "summary": {
            "total_dq_events": len(failures),
            "tables_with_issues": list(by_table.keys()),
            "most_common_failure": most_common,
            "total_anomalies": len(anomalies),
        },
        "by_table": {k: {"failures": v} for k, v in by_table.items()},
        "recent_failures": failures[:10],
        "recent_anomalies": anomalies[:5],
        "last_updated": datetime.now().isoformat(),
    }


@app.get("/api/news/search")
async def search_news(q: str = Query(..., min_length=2), limit: int = 5):
    """
    Full-text search po artykułach BBC + AI summary z Groq.
    Przykład: GET /api/news/search?q=bitcoin+inflation
    """
    from groq import Groq

    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    articles = (
        execute_query(
            """
        SELECT title, description, source, url, published_at, sentiment_score,
               ts_rank(
                   to_tsvector('english', title || ' ' || COALESCE(description, '')),
                   plainto_tsquery('english', :q)
               ) as relevance
        FROM news_articles
        WHERE to_tsvector('english', title || ' ' || COALESCE(description, ''))
              @@ plainto_tsquery('english', :q)
        ORDER BY relevance DESC, published_at DESC
        LIMIT :limit
        """,
            {"q": q, "limit": limit},
        )
        or []
    )

    if not articles:
        return {"query": q, "articles": [], "ai_summary": "No relevant articles found."}

    context = "\n".join([f"- [{str(a['published_at'])[:10]}] {a['title']}: {str(a.get('description', ''))[:100]}" for a in articles])

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Based on these recent news articles:\n{context}\n\nAnswer in 2-3 sentences: {q}"}],
            temperature=0.3,
            max_tokens=200,
        )
        content = resp.choices[0].message.content
        ai_summary = content.strip() if content else "No summary generated."
    except Exception as e:
        ai_summary = f"AI summary unavailable: {str(e)}"

    return {
        "query": q,
        "articles_found": len(articles),
        "articles": articles,
        "ai_summary": ai_summary,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
