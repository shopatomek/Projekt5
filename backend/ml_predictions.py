# backend/ml_predictions.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import numpy as np
from sklearn.linear_model import LinearRegression  # type: ignore
from sklearn.preprocessing import StandardScaler  # type: ignore

from database import execute_query

logger = logging.getLogger(__name__)


def _build_features(timestamps: List[datetime]) -> np.ndarray:
    """Extract time-based features from a list of datetime objects."""
    features = []
    for ts in timestamps:
        unix = ts.timestamp()
        hour_sin = np.sin(2 * np.pi * ts.hour / 24)
        hour_cos = np.cos(2 * np.pi * ts.hour / 24)
        dow_sin = np.sin(2 * np.pi * ts.weekday() / 7)
        dow_cos = np.cos(2 * np.pi * ts.weekday() / 7)
        features.append([unix, hour_sin, hour_cos, dow_sin, dow_cos])
    return np.array(features)


def predict_price(symbol: str, horizon_hours: int = 24) -> Dict[str, Any]:
    """
    Trains a LinearRegression model on the last 7 days of price data
    and returns a forecast for the next `horizon_hours` hours.
    """
    rows = (
        execute_query(
            """
        SELECT price_usd, timestamp
        FROM crypto_prices
        WHERE symbol = :symbol
          AND timestamp >= NOW() - INTERVAL '7 days'
          AND price_usd > 0
        ORDER BY timestamp ASC
    """,
            {"symbol": symbol.upper()},
        )
        or []
    )

    if len(rows) < 10:
        raise ValueError(f"Insufficient data for {symbol}: only {len(rows)} rows available. Need at least 10.")

    prices = np.array([float(r["price_usd"]) for r in rows])
    timestamps = [datetime.fromisoformat(str(r["timestamp"])) for r in rows]

    X_train = _build_features(timestamps)
    y_train = prices

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    model = LinearRegression()
    model.fit(X_scaled, y_train)

    y_pred_train = model.predict(X_scaled)
    residuals = np.abs(y_train - y_pred_train)
    mae = float(np.mean(residuals))
    std_residual = float(np.std(residuals))

    last_ts = timestamps[-1]
    future_timestamps = [last_ts + timedelta(hours=i + 1) for i in range(horizon_hours)]
    X_future = _build_features(future_timestamps)
    X_future_scaled = scaler.transform(X_future)
    y_future = model.predict(X_future_scaled)

    ci = 1.96 * std_residual  # approx 95% confidence interval
    forecast = [
        {
            "timestamp": ts.isoformat(),
            "predicted_price": round(float(price), 2),
            "lower_bound": round(max(0.0, float(price) - ci), 2),
            "upper_bound": round(float(price) + ci, 2),
        }
        for ts, price in zip(future_timestamps, y_future)
    ]

    return {
        "symbol": symbol.upper(),
        "model": "LinearRegression",
        "training_points": len(rows),
        "horizon_hours": horizon_hours,
        "forecast": forecast,
        "last_known_price": round(float(prices[-1]), 2),
        "mae_usd": round(mae, 2),
    }
