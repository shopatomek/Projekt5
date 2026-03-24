# backend/data_quality.py

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

# Pobieranie danych połączenia z .env
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")


# Funkcja do łączenia się z bazą danych
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )


# Funkcja do sprawdzania jakości danych dla kryptowalut
def check_crypto_data_quality(symbol, price_usd, volume_24h, price_change_24h):
    issues = []

    if price_usd <= 0:
        issues.append(f"Invalid price for {symbol}: {price_usd}")

    if volume_24h < 0:
        issues.append(f"Negative volume for {symbol}: {volume_24h}")

    if abs(price_change_24h) > 100:
        issues.append(f"Unrealistic price change for {symbol}: {price_change_24h}%")

    return issues


# Funkcja do sprawdzania jakości danych dla pogody
def check_weather_data_quality(city, temperature, humidity, weather_condition):
    issues = []

    if temperature < -50 or temperature > 50:
        issues.append(f"Invalid temperature for {city}: {temperature}°C")

    if humidity < 0 or humidity > 100:
        issues.append(f"Invalid humidity for {city}: {humidity}%")

    if not weather_condition:
        issues.append(f"Missing weather condition for {city}")

    return issues


# Funkcja do sprawdzania jakości danych dla newsów
def check_news_data_quality(title, description, source, url, published_at):
    issues = []

    if not title:
        issues.append("Missing title")

    if not source:
        issues.append("Missing source")

    if not url:
        issues.append("Missing URL")

    if not published_at:
        issues.append("Missing published_at")

    return issues


# Funkcja do uruchamiania sprawdzania jakości danych po INSERT
def run_data_quality_checks(table_name, data):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if table_name == "crypto_prices":
            issues = check_crypto_data_quality(**data)
        elif table_name == "weather_data":
            issues = check_weather_data_quality(**data)
        elif table_name == "news_articles":
            issues = check_news_data_quality(**data)
        else:
            issues = []

        if issues:
            print(f"Data quality issues for {table_name}: {issues}")
            # Możesz tu dodać logowanie do bazy danych lub wysyłanie alertów

    finally:
        cursor.close()
        conn.close()


# # Przykład użycia
if __name__ == "__main__":
    # Przykładowe dane
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
