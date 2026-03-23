from database import execute_query


def calculate_crypto_kpis():
    """
    Oblicza kluczowe wskaźniki dla kryptowalut na podstawie danych z CoinCap (pobranych przez n8n).
    """
    try:
        # Pobieramy najnowsze ceny z bazy
        # Zmieniamy price_change_24h na change_percent_24h jeśli tak mapujesz w n8n
        query = """
        SELECT symbol, price_usd, price_change_24h, market_cap 
        FROM crypto_prices 
        WHERE timestamp IN (SELECT MAX(timestamp) FROM crypto_prices GROUP BY symbol)
        """
        prices = execute_query(query)

        # Pobieramy statystyki z widoku zdefiniowanego w init.sql
        stats_query = "SELECT * FROM daily_crypto_stats ORDER BY date DESC LIMIT 10"
        stats = execute_query(stats_query)

        # Wyznaczanie prostego sentymentu na podstawie zmian cen
        sentiment = "Neutral"
        if prices:
            avg_change = sum(
                float(p.get("price_change_24h") or 0) for p in prices
            ) / len(prices)
            if avg_change > 1:
                sentiment = "Bullish"
            elif avg_change < -1:
                sentiment = "Bearish"

        return {
            "prices": prices if prices else [],
            "daily_stats": stats if stats else [],
            "market_sentiment": sentiment,
        }
    except Exception as e:
        print(f"Błąd w calculate_crypto_kpis: {e}")
        return {"prices": [], "daily_stats": [], "market_sentiment": "Unknown"}


def calculate_stock_kpis():
    """
    Analizuje zmiany na rynku akcji.
    """
    try:
        # Pobieramy dane o akcjach
        query = """
        SELECT symbol, close_price, trading_date 
        FROM stock_prices 
        ORDER BY trading_date DESC, symbol ASC 
        LIMIT 20
        """
        stocks = execute_query(query)

        # Logika obliczania wydajności sektora (uproszczona)
        sector_perf = "Market Stable"
        if stocks:
            sector_perf = "Technology: Active"

        return {
            "daily_changes": stocks if stocks else [],
            "sector_performance": sector_perf,
        }
    except Exception as e:
        print(f"Błąd w calculate_stock_kpis: {e}")
        return {"daily_changes": [], "sector_performance": "N/A"}
