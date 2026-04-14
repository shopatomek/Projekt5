import pytest
from datetime import datetime, timezone, timedelta
from data_quality.checks import (
    NotNullCheck,
    RangeCheck,
    UrlFormatCheck,
    FutureTimestampCheck,
)


class TestNotNullCheck:
    def test_valid_not_null_string(self):
        check = NotNullCheck("name")
        record = {"name": "Bitcoin"}
        assert check.validate(record) is True

    def test_null_value(self):
        check = NotNullCheck("name")
        record = {"name": None}
        assert check.validate(record) is False

    def test_empty_string(self):
        check = NotNullCheck("name")
        record = {"name": ""}
        assert check.validate(record) is False

    def test_missing_key(self):
        check = NotNullCheck("name")
        record = {}
        assert check.validate(record) is False

    def test_fix_does_nothing(self):
        check = NotNullCheck("name")
        record = {"name": None}
        fixed = check.fix(record)
        assert fixed == record  # nie naprawia


class TestRangeCheck:
    def test_valid_within_range(self):
        check = RangeCheck("price", min_val=0, max_val=100)
        assert check.validate({"price": 50}) is True

    def test_below_min(self):
        check = RangeCheck("price", min_val=0)
        assert check.validate({"price": -10}) is False

    def test_above_max(self):
        check = RangeCheck("price", max_val=100)
        assert check.validate({"price": 150}) is False

    def test_exclusive_min(self):
        check = RangeCheck("price", min_val=0, exclusive_min=True)
        assert check.validate({"price": 0}) is False
        assert check.validate({"price": 0.01}) is True

    def test_nullable_allowed(self):
        check = RangeCheck("price", min_val=0, nullable=True)
        assert check.validate({"price": None}) is True

    def test_nullable_not_allowed(self):
        check = RangeCheck("price", min_val=0, nullable=False)
        assert check.validate({"price": None}) is False

    def test_non_numeric_value(self):
        check = RangeCheck("price")
        assert check.validate({"price": "not a number"}) is False

    def test_fix_clips_to_max(self):
        check = RangeCheck("humidity", min_val=0, max_val=100)
        record = {"humidity": 150}
        fixed = check.fix(record)
        assert fixed["humidity"] == 100

    def test_fix_clips_to_min(self):
        check = RangeCheck("humidity", min_val=0, max_val=100)
        record = {"humidity": -20}
        fixed = check.fix(record)
        assert fixed["humidity"] == 0

    def test_fix_does_not_clip_non_repairable_field(self):
        check = RangeCheck("price", min_val=0, max_val=100)
        record = {"price": 150}
        fixed = check.fix(record)
        assert fixed["price"] == 150  # brak naprawy


class TestUrlFormatCheck:
    def test_valid_http_url(self):
        check = UrlFormatCheck("url")
        assert check.validate({"url": "http://example.com"}) is True

    def test_valid_https_url(self):
        check = UrlFormatCheck("url")
        assert check.validate({"url": "https://bbc.com/news"}) is True

    def test_invalid_url_no_protocol(self):
        check = UrlFormatCheck("url")
        assert check.validate({"url": "example.com"}) is False

    def test_empty_string(self):
        check = UrlFormatCheck("url")
        assert check.validate({"url": ""}) is False

    def test_none_value(self):
        check = UrlFormatCheck("url")
        assert check.validate({"url": None}) is False

    def test_fix_does_nothing(self):
        check = UrlFormatCheck("url")
        record = {"url": "not-a-url"}
        fixed = check.fix(record)
        assert fixed == record


class TestFutureTimestampCheck:
    def test_past_timestamp_valid(self):
        check = FutureTimestampCheck("timestamp", max_future_minutes=5)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        assert check.validate({"timestamp": past}) is True

    def test_current_timestamp_valid(self):
        check = FutureTimestampCheck("timestamp", max_future_minutes=5)
        now = datetime.now(timezone.utc)
        assert check.validate({"timestamp": now}) is True

    def test_future_timestamp_within_window_valid(self):
        check = FutureTimestampCheck("timestamp", max_future_minutes=5)
        future = datetime.now(timezone.utc) + timedelta(minutes=3)
        assert check.validate({"timestamp": future}) is True

    def test_future_timestamp_beyond_window_invalid(self):
        check = FutureTimestampCheck("timestamp", max_future_minutes=5)
        future = datetime.now(timezone.utc) + timedelta(minutes=10)
        assert check.validate({"timestamp": future}) is False

    def test_none_value_valid(self):
        check = FutureTimestampCheck("timestamp")
        assert check.validate({"timestamp": None}) is True

    def test_non_datetime_value(self):
        check = FutureTimestampCheck("timestamp")
        assert check.validate({"timestamp": "2025-01-01"}) is True  # przepuszcza, bo inny check wyłapie

    def test_fix_does_nothing(self):
        check = FutureTimestampCheck("timestamp")
        record = {"timestamp": datetime.now(timezone.utc) + timedelta(days=1)}
        fixed = check.fix(record)
        assert fixed == record
