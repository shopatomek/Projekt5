# backend/tests/test_ml_predictions.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from ml_predictions import predict_price, _build_features


class TestBuildFeatures:
    def test_build_features_returns_correct_shape(self):
        timestamps = [datetime(2026, 4, 1, 12, 0, 0), datetime(2026, 4, 1, 13, 0, 0)]
        features = _build_features(timestamps)
        assert features.shape == (2, 5)  # 2 timestamps, 5 features
        assert all(isinstance(val, float) for val in features[0])


class TestPredictPrice:
    @patch("ml_predictions.execute_query")
    def test_predict_price_returns_expected_structure(self, mock_query):
        # Mock data – 24 godziny danych (co godzinę)
        mock_rows = []
        base_ts = datetime(2026, 4, 20, 0, 0, 0)
        for i in range(24):  # 24 punkty
            mock_rows.append({"price_usd": 70000 + i * 100, "timestamp": (base_ts + timedelta(hours=i)).isoformat()})  # trend wzrostowy
        mock_query.return_value = mock_rows

        result = predict_price("BTC", horizon_hours=6)

        # Sprawdź strukturę odpowiedzi
        assert result["symbol"] == "BTC"
        assert result["model"] == "LinearRegression"
        assert result["training_points"] == 24
        assert result["horizon_hours"] == 6
        assert len(result["forecast"]) == 6
        assert "predicted_price" in result["forecast"][0]
        assert "lower_bound" in result["forecast"][0]
        assert "upper_bound" in result["forecast"][0]
        assert result["last_known_price"] > 0
        assert "mae_usd" in result

    @patch("ml_predictions.execute_query")
    def test_predict_price_insufficient_data_raises_error(self, mock_query):
        # Mniej niż 10 punktów
        mock_query.return_value = [{"price_usd": 70000, "timestamp": datetime.now().isoformat()}] * 5

        with pytest.raises(ValueError, match="Insufficient data"):
            predict_price("BTC", horizon_hours=6)

    @patch("ml_predictions.execute_query")
    def test_predict_price_handles_empty_data(self, mock_query):
        mock_query.return_value = []

        with pytest.raises(ValueError, match="Insufficient data"):
            predict_price("BTC", horizon_hours=6)
