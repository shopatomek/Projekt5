from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
from datetime import datetime

from database import execute_query
from analytics import calculate_crypto_kpis, calculate_stock_kpis
from ai_insights import generate_daily_summary, analyze_trend

app = FastAPI(title="AI Business Intelligence Dashboard")

# CORS dla frontendu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "AI Dashboard API running", "version": "1.0.0", "source": "CoinCap API"}


@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    try:
        crypto_kpis = calculate_crypto_kpis()
        stock_kpis = calculate_stock_kpis()

        # Pobierz najnowsze newsy
        news_query = """
        SELECT title, description, source, published_at
        FROM news_articles
        ORDER BY published_at DESC
        LIMIT 10
        """
        news = execute_query(news_query)

        # Pobierz pogodę
        weather_query = """
        SELECT city, temperature, humidity, weather_condition
        FROM weather_data
        ORDER BY timestamp DESC
        LIMIT 1
        """
        weather = execute_query(weather_query)

        return {"crypto": crypto_kpis, "stocks": stock_kpis, "news": news, "weather": weather[0] if weather else None, "timestamp": str(datetime.now())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/daily-summary")
async def get_ai_daily_summary():
    try:
        # Sprawdzenie czy są jakiekolwiek dane pogodowe przed zapytaniem
        weather_data = execute_query("SELECT temperature, humidity FROM weather_data ORDER BY timestamp DESC LIMIT 1")
        news_count_data = execute_query("SELECT COUNT(*) as count FROM news_articles WHERE DATE(published_at) = CURRENT_DATE")

        metrics = {
            "crypto_data": calculate_crypto_kpis().get("prices", []),
            "stock_data": calculate_stock_kpis().get("daily_changes", []),
            "news_count": news_count_data[0]["count"] if news_count_data else 0,
            "weather": weather_data[0] if weather_data else {},
        }

        summary = generate_daily_summary(metrics)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/crypto-trend")
async def get_crypto_trend(symbol: str = "bitcoin", days: int = 7):
    try:
        # Naprawione zapytanie SQL (poprawne bindowanie interwału dla Postgres)
        query = f"""
        SELECT price_usd as value, timestamp
        FROM crypto_prices
        WHERE symbol = :symbol
        AND timestamp >= NOW() - INTERVAL '{days} days'
        ORDER BY timestamp
        """

        data = execute_query(query, {"symbol": symbol})

        # Generuj AI trend analysis
        trend_analysis = analyze_trend(data, f"{symbol.capitalize()} price")

        return {"symbol": symbol, "data": data, "ai_analysis": trend_analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
