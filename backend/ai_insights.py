# backend/ai_insights.py
import os
import json
import google.generativeai as genai
from datetime import datetime
from typing import Dict, List

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def generate_daily_summary(metrics: Dict) -> Dict:
    """
    Generuje dzienny raport AI z metryk biznesowych

    Args:
        metrics: dict zawierający:
          - crypto_data: list[dict] z cenami krypto
          - stock_data: list[dict] z cenami akcji
          - news_count: int
          - weather: dict z pogodą

    Returns:
        dict: {
          'summary': str - krótkie podsumowanie,
          'insights': list[str] - kluczowe spostrzeżenia,
          'recommendations': list[str] - rekomendacje
        }
    """

    prompt = f"""
Jesteś ekspertem analityki biznesowej. Przeanalizuj dzisiejsze dane i wygeneruj raport:

DANE Z DZIŚ ({datetime.now().strftime('%Y-%m-%d')}):

Kryptowaluty:
{json.dumps(metrics.get('crypto_data', []), indent=2)}

Akcje:
{json.dumps(metrics.get('stock_data', []), indent=2)}

Liczba newsów: {metrics.get('news_count', 0)}

Pogoda: {json.dumps(metrics.get('weather', {}), indent=2)}

WYGENERUJ:
1. Krótkie podsumowanie dnia (2-3 zdania) - ogólny ton rynku
2. Top 3 najważniejsze spostrzeżenia (konkretne liczby i trendy)
3. 2-3 rekomendacje działań dla biznesu

ODPOWIEDŹ W FORMACIE JSON (tylko JSON, bez dodatkowego tekstu):
{{
  "summary": "...",
  "insights": ["...", "...", "..."],
  "recommendations": ["...", "..."]
}}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Usuń markdown backticks jeśli są
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        result = json.loads(text.strip())
        result["generated_at"] = datetime.now().isoformat()
        return result

    except Exception as e:
        print(f"Błąd generowania AI insights: {e}")
        return {"summary": "Brak dostępnych insightów AI", "insights": [], "recommendations": [], "error": str(e)}


def analyze_trend(data_points: List[Dict], metric_name: str) -> str:
    """
    Analizuje trend w danych czasowych

    Args:
        data_points: lista dict z kluczem 'value' i 'timestamp'
        metric_name: nazwa metryki (np. 'Bitcoin price')

    Returns:
        str: Analiza trendu od AI
    """

    if not data_points or len(data_points) < 2:
        return "Insufficient data for trend analysis"

    prompt = f"""
Przeanalizuj trend dla metryki: {metric_name}

Dane (chronologicznie):
{json.dumps(data_points, indent=2)}

Opisz:
1. Jaki jest trend (wzrostowy/spadkowy/stabilny)?
2. O ile procent zmienił się w tym okresie?
3. Czy są zauważalne anomalie lub spike'i?

Odpowiedź w 2-3 zdaniach, konkretnie i liczbowo.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Trend analysis error: {str(e)}"


def explain_anomaly(anomaly_data: Dict) -> str:
    """
    Wyjaśnia wykrytą anomalię w danych
    """

    prompt = f"""
Wykryto anomalię w danych:

{json.dumps(anomaly_data, indent=2)}

Wyjaśnij krótko (2-3 zdania):
1. Co mogło spowodować tę anomalię?
2. Czy to powód do niepokoju?
3. Jakie są możliwe następstwa?
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Unable to explain anomaly: {str(e)}"
