from datetime import datetime, timezone, timedelta
from unittest.mock import patch


class TestDataQualityEngine:
    def test_engine_run_on_crypto_prices(self):
        from data_quality.engine import engine
        from data_quality.reporters import LogReporter

        engine.set_reporters([LogReporter()])

        test_record = {
            "symbol": "BTC",
            "price_usd": 50000,
            "volume_24h": 1000000,
            "price_change_24h": 2.5,
            "timestamp": datetime.now(timezone.utc),
        }

        report, cleaned = engine.run("crypto_prices", test_record, record_id="BTC")

        assert report.passed is True
        assert report.failed_checks == []
        assert report.table == "crypto_prices"
        assert report.record_id == "BTC"

    def test_engine_run_with_future_timestamp(self):
        from data_quality.engine import engine
        from data_quality.reporters import LogReporter

        engine.set_reporters([LogReporter()])

        future = datetime.now(timezone.utc) + timedelta(days=365)
        test_record = {
            "symbol": "BTC",
            "price_usd": 50000,
            "volume_24h": 1000000,
            "price_change_24h": 2.5,
            "timestamp": future,
        }

        report, cleaned = engine.run("crypto_prices", test_record, record_id="BTC")

        assert report.passed is False
        assert "FutureTimestampCheck:timestamp" in report.failed_checks

    def test_engine_run_missing_table(self):
        from data_quality.engine import engine
        from data_quality.reporters import LogReporter

        engine.set_reporters([LogReporter()])

        report, cleaned = engine.run("non_existent_table", {"some": "data"})

        assert report.passed is True
        assert report.total_checks == 0

    def test_engine_run_weather_data(self):
        from data_quality.engine import engine
        from data_quality.reporters import LogReporter

        engine.set_reporters([LogReporter()])

        test_record = {
            "city": "Warsaw",
            "temperature": 20.5,
            "humidity": 60,
            "weather_condition": "sunny",
        }

        report, cleaned = engine.run("weather_data", test_record, record_id="Warsaw")

        assert report.passed is True
        assert report.failed_checks == []

    def test_engine_run_news_articles(self):
        from data_quality.engine import engine
        from data_quality.reporters import LogReporter

        engine.set_reporters([LogReporter()])

        test_record = {
            "title": "Bitcoin rises",
            "source": "BBC News",
            "url": "https://bbc.com/news/123",
            "published_at": datetime.now(timezone.utc),
        }

        report, cleaned = engine.run("news_articles", test_record, record_id="test_news")

        assert report.passed is True
        assert report.failed_checks == []

    def test_engine_run_news_articles_missing_title(self):
        from data_quality.engine import engine
        from data_quality.reporters import LogReporter

        engine.set_reporters([LogReporter()])

        test_record = {
            "title": "",
            "source": "BBC News",
            "url": "https://bbc.com/news/123",
            "published_at": datetime.now(timezone.utc),
        }

        report, cleaned = engine.run("news_articles", test_record, record_id="test_news")

        assert report.passed is False
        assert "NotNullCheck:title" in report.failed_checks


class TestDatabaseReporter:
    def test_database_reporter_only_reports_failures(self):
        """Test że reporter nie zapisuje sukcesów"""
        from data_quality.reporters import DatabaseReporter
        from data_quality.engine import DQReport
        from datetime import datetime, timezone

        reporter = DatabaseReporter()

        passed_report = DQReport(
            table="crypto_prices",
            passed=True,
            failed_checks=[],
            original_record={},
            fixed_record={},
            auto_repaired=False,
            checked_at=datetime.now(timezone.utc).isoformat(),
            record_id="BTC",
            total_checks=5,
        )

        # Mockujemy execute_query w module database (tam gdzie jest faktycznie importowane)
        with patch("database.execute_query") as mock_query:
            reporter.report(passed_report)
            # Nie powinien wywołać execute_query dla passed=True
            mock_query.assert_not_called()

    def test_database_reporter_inserts_on_failure(self):
        """Test że reporter zapisuje błędy"""
        from data_quality.reporters import DatabaseReporter
        from data_quality.engine import DQReport
        from datetime import datetime, timezone

        reporter = DatabaseReporter()

        failed_report = DQReport(
            table="crypto_prices",
            passed=False,
            failed_checks=["RangeCheck:price_usd"],
            original_record={"price_usd": -100},
            fixed_record={"price_usd": 0},
            auto_repaired=True,
            checked_at=datetime.now(timezone.utc).isoformat(),
            record_id="BTC",
            total_checks=5,
        )

        # Mockujemy execute_query w module database
        with patch("database.execute_query") as mock_query:
            mock_query.return_value = None
            reporter.report(failed_report)
            # Powinien wywołać execute_query
            mock_query.assert_called_once()
