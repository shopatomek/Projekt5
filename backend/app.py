# backend/app.py
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
    allow_origins=["*"],  # W produkcji: konkretne domeny
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "AI Dashboard API running", "version": "1.0.0"}


@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """
    Główny endpoint - zwraca wszystkie dane dla dashboardu
    """
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
    """
    Generuje AI summary całego dnia
    """
    try:
        # Zbierz metryki
        metrics = {
            "crypto_data": calculate_crypto_kpis().get("prices", []),
            "stock_data": calculate_stock_kpis().get("daily_changes", []),
            "news_count": execute_query("SELECT COUNT(*) as count FROM news_articles WHERE DATE(published_at) = CURRENT_DATE")[0]["count"],
            "weather": execute_query("SELECT temperature, humidity FROM weather_data ORDER BY timestamp DESC LIMIT 1")[0] if execute_query("SELECT 1 FROM weather_data LIMIT 1") else {},
        }

        # Generuj AI insights
        summary = generate_daily_summary(metrics)

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/crypto-trend")
async def get_crypto_trend(symbol: str = "bitcoin", days: int = 7):
    """
    Time-series data dla wykresu kryptowaluty
    """
    try:
        query = """
        SELECT price_usd as value, timestamp
        FROM crypto_prices
        WHERE symbol = :symbol
        AND timestamp >= NOW() - INTERVAL ':days days'
        ORDER BY timestamp
        """

        data = execute_query(query, {"symbol": symbol, "days": days})

        # Generuj AI trend analysis
        trend_analysis = analyze_trend(data, f"{symbol.capitalize()} price")

        return {"symbol": symbol, "data": data, "ai_analysis": trend_analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
