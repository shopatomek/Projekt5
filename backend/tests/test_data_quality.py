# tests/test_data_quality.py
import json
from unittest.mock import MagicMock, patch
from data_quality import (
    check_crypto_data_quality,
    check_weather_data_quality,
    check_news_data_quality,
    run_data_quality_checks,
)


def log_test_result(
    test_name, input_data, expected, result, status, error_message=None
):
    test_result = {
        "test_name": test_name,
        "input_data": input_data,
        "expected": expected,
        "result": result,
        "status": status,
        "error_message": error_message,
    }
    print(json.dumps(test_result, indent=2, ensure_ascii=False))


def test_check_crypto_data_quality_valid():
    crypto_data = {
        "symbol": "BTC",
        "price_usd": 50000,
        "volume_24h": 1000000,
        "price_change_24h": 2.5,
    }
    issues = check_crypto_data_quality(**crypto_data)
    expected = []
    result = issues

    try:
        assert issues == expected, f"Oczekiwano brak błędów, ale wykryto: {issues}"
        log_test_result(
            test_name="test_check_crypto_data_quality_valid",
            input_data=crypto_data,
            expected=expected,
            result=result,
            status="PASSED",
        )
    except AssertionError as e:
        log_test_result(
            test_name="test_check_crypto_data_quality_valid",
            input_data=crypto_data,
            expected=expected,
            result=result,
            status="FAILED",
            error_message=str(e),
        )
        raise


def test_check_crypto_data_quality_invalid():
    crypto_data = {
        "symbol": "BTC",
        "price_usd": -100,
        "volume_24h": 1000000,
        "price_change_24h": 2.5,
    }
    issues = check_crypto_data_quality(**crypto_data)
    expected = ["Invalid price for BTC: -100"]
    result = issues

    try:
        assert expected[0] in issues, "Błąd ujemnej ceny nie został wykryty!"
        log_test_result(
            test_name="test_check_crypto_data_quality_invalid",
            input_data=crypto_data,
            expected=expected,
            result=result,
            status="PASSED",
        )
    except AssertionError as e:
        log_test_result(
            test_name="test_check_crypto_data_quality_invalid",
            input_data=crypto_data,
            expected=expected,
            result=result,
            status="FAILED",
            error_message=str(e),
        )
        raise


def test_check_weather_data_quality_valid():
    weather_data = {
        "city": "Warsaw",
        "temperature": 20.5,
        "humidity": 60,
        "weather_condition": "sunny",
    }
    issues = check_weather_data_quality(**weather_data)
    expected = []
    result = issues

    try:
        assert issues == expected, f"Oczekiwano brak błędów, ale wykryto: {issues}"
        log_test_result(
            test_name="test_check_weather_data_quality_valid",
            input_data=weather_data,
            expected=expected,
            result=result,
            status="PASSED",
        )
    except AssertionError as e:
        log_test_result(
            test_name="test_check_weather_data_quality_valid",
            input_data=weather_data,
            expected=expected,
            result=result,
            status="FAILED",
            error_message=str(e),
        )
        raise


def test_check_weather_data_quality_invalid():
    weather_data = {
        "city": "Warsaw",
        "temperature": -60,
        "humidity": 60,
        "weather_condition": "sunny",
    }
    issues = check_weather_data_quality(**weather_data)
    expected = ["Invalid temperature for Warsaw: -60°C"]
    result = issues

    try:
        assert expected[0] in issues, "Błąd temperatury nie został wykryty!"
        log_test_result(
            test_name="test_check_weather_data_quality_invalid",
            input_data=weather_data,
            expected=expected,
            result=result,
            status="PASSED",
        )
    except AssertionError as e:
        log_test_result(
            test_name="test_check_weather_data_quality_invalid",
            input_data=weather_data,
            expected=expected,
            result=result,
            status="FAILED",
            error_message=str(e),
        )
        raise


def test_check_news_data_quality_valid():
    news_data = {
        "title": "Bitcoin Price Surges",
        "description": "Bitcoin price has surged by 10%.",
        "source": "BBC Business",
        "url": "https://bbc.com/news/123",
        "published_at": "2026-03-24T12:00:00Z",
    }
    issues = check_news_data_quality(**news_data)
    expected = []
    result = issues

    try:
        assert issues == expected, f"Oczekiwano brak błędów, ale wykryto: {issues}"
        log_test_result(
            test_name="test_check_news_data_quality_valid",
            input_data=news_data,
            expected=expected,
            result=result,
            status="PASSED",
        )
    except AssertionError as e:
        log_test_result(
            test_name="test_check_news_data_quality_valid",
            input_data=news_data,
            expected=expected,
            result=result,
            status="FAILED",
            error_message=str(e),
        )
        raise


def test_check_news_data_quality_invalid():
    news_data = {
        "title": "",
        "description": "Bitcoin price has surged by 10%.",
        "source": "BBC Business",
        "url": "https://bbc.com/news/123",
        "published_at": "2026-03-24T12:00:00Z",
    }
    issues = check_news_data_quality(**news_data)
    expected = ["Missing title"]
    result = issues

    try:
        assert expected[0] in issues, "Błąd braku tytułu nie został wykryty!"
        log_test_result(
            test_name="test_check_news_data_quality_invalid",
            input_data=news_data,
            expected=expected,
            result=result,
            status="PASSED",
        )
    except AssertionError as e:
        log_test_result(
            test_name="test_check_news_data_quality_invalid",
            input_data=news_data,
            expected=expected,
            result=result,
            status="FAILED",
            error_message=str(e),
        )
        raise


def test_run_data_quality_checks_crypto():
    crypto_data = {
        "symbol": "BTC",
        "price_usd": 50000,
        "volume_24h": 1000000,
        "price_change_24h": 2.5,
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    input_data = {"table_name": "crypto_prices", "data": crypto_data}

    try:
        with patch("data_quality.get_db_connection", return_value=mock_conn):
            run_data_quality_checks("crypto_prices", crypto_data)
            assert mock_cursor.close.called
            assert mock_conn.close.called
            log_test_result(
                test_name="test_run_data_quality_checks_crypto",
                input_data=input_data,
                expected="Funkcja `run_data_quality_checks` została wywołana poprawnie",
                result="Funkcja `run_data_quality_checks` została wywołana poprawnie",
                status="PASSED",
            )
    except AssertionError as e:
        log_test_result(
            test_name="test_run_data_quality_checks_crypto",
            input_data=input_data,
            expected="Funkcja `run_data_quality_checks` została wywołana poprawnie",
            result=str(e),
            status="FAILED",
            error_message=str(e),
        )
        raise


def test_run_data_quality_checks_news():
    news_data = {
        "title": "",
        "description": "Bitcoin price has surged by 10%.",
        "source": "BBC Business",
        "url": "https://bbc.com/news/123",
        "published_at": "2026-03-24T12:00:00Z",
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    input_data = {"table_name": "news_articles", "data": news_data}

    try:
        with patch("data_quality.get_db_connection", return_value=mock_conn):
            run_data_quality_checks("news_articles", news_data)
            assert mock_cursor.close.called
            assert mock_conn.close.called
            log_test_result(
                test_name="test_run_data_quality_checks_news",
                input_data=input_data,
                expected="Funkcja `run_data_quality_checks` została wywołana poprawnie",
                result="Funkcja `run_data_quality_checks` została wywołana poprawnie",
                status="PASSED",
            )
    except AssertionError as e:
        log_test_result(
            test_name="test_run_data_quality_checks_news",
            input_data=input_data,
            expected="Funkcja `run_data_quality_checks` została wywołana poprawnie",
            result=str(e),
            status="FAILED",
            error_message=str(e),
        )
        raise
