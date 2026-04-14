import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_fetch_initial_news_and_weather_success():
    """Test udanego pobrania newsów i pogody"""
    from app import fetch_initial_news_and_weather

    # Mock RSS response
    mock_rss_xml = """
    <rss>
      <channel>
        <item>
          <title>Test News</title>
          <description>Test description</description>
          <link>https://bbc.com/test</link>
          <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    # Mock weather response
    mock_weather_json = {
        "current": {
            "temperature_2m": 15.5,
            "relative_humidity_2m": 65,
            "weather_code": 0,
        }
    }

    with patch("app.execute_query") as mock_execute:
        # Mock dla newsów – brak istniejących
        mock_execute.side_effect = [
            None,  # SELECT COUNT(*) dla news_cnt (brak)
            None,  # INSERT news_articles
            None,  # INSERT weather_data
        ]

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            # Mock odpowiedzi RSS
            mock_rss_response = AsyncMock()
            mock_rss_response.text = mock_rss_xml
            mock_client.get.return_value = mock_rss_response

            # Mock odpowiedzi pogodowej
            mock_weather_response = AsyncMock()
            mock_weather_response.json.return_value = mock_weather_json
            # drugie wywołanie get() zwraca pogodę
            mock_client.get.return_value = mock_weather_response

            # Uruchom funkcję
            await fetch_initial_news_and_weather()

            # Asercje
            assert mock_client.get.call_count >= 2
            mock_execute.assert_called()


@pytest.mark.asyncio
async def test_fetch_initial_news_and_weather_news_failure():
    """Test obsługi błędu przy pobieraniu newsów"""
    from app import fetch_initial_news_and_weather

    with patch("app.execute_query") as mock_execute:
        mock_execute.side_effect = Exception("DB error")

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Network error")

            # Nie powinno rzucić wyjątkiem – funkcja łapie błędy
            await fetch_initial_news_and_weather()
            # Jeśli doszło do tego miejsca – test OK


@pytest.mark.asyncio
async def test_fetch_initial_news_and_weather_generates_summary():
    """Test generowania Daily Summary po pobraniu danych"""
    from app import fetch_initial_news_and_weather

    with patch("app.execute_query") as mock_execute:
        # Symulujemy że są newsy w bazie po zapisie
        mock_execute.side_effect = [
            [{"cnt": 0}],  # pierwsze SELECT COUNT(*) – brak
            None,  # INSERT news
            None,  # INSERT weather
            [{"cnt": 5}],  # drugie SELECT COUNT(*) – już są
            [{"temperature": 15, "humidity": 60}],  # weather_row
            [{"count": 5}],  # news_count_today
        ]

        with patch("app.generate_daily_summary") as mock_summary:
            mock_summary.return_value = {"summary": "Test summary"}
            with patch("app.calculate_crypto_kpis") as mock_kpis:
                mock_kpis.return_value = {"prices": []}
                with patch("httpx.AsyncClient") as MockClient:
                    mock_client = AsyncMock()
                    MockClient.return_value.__aenter__.return_value = mock_client
                    mock_rss = AsyncMock()
                    mock_rss.text = (
                        "<rss><channel><item><title>Test</title><description>Desc</description><link>https://bbc.com</link><pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate></item></channel></rss>"
                    )
                    mock_weather = AsyncMock()
                    mock_weather.json.return_value = {"current": {"temperature_2m": 15, "relative_humidity_2m": 60, "weather_code": 0}}
                    mock_client.get.return_value = mock_rss
                    # drugie wywołanie get – dla pogody
                    mock_client.get.side_effect = [mock_rss, mock_weather]

                    await fetch_initial_news_and_weather()

                    # Sprawdź czy generate_daily_summary zostało wywołane
                    mock_summary.assert_called_once()
