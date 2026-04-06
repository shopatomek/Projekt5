# backend/ai_insights.py

import os
import json
from groq import Groq
from datetime import datetime
from typing import Dict, List

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def generate_daily_summary(metrics: Dict) -> Dict:
    
    prompt = f"""Jesteś ekspertem analityki biznesowej. Przeanalizuj dzisiejsze dane i wygeneruj raport:

DANE Z DZIŚ ({datetime.now().strftime("%Y-%m-%d")}):

Kryptowaluty:
{json.dumps(metrics.get("crypto_data", []), indent=2)}

Liczba newsów: {metrics.get("news_count", 0)}

Pogoda: {json.dumps(metrics.get("weather", {}), indent=2)}

WYGENERUJ:
1. Krótkie podsumowanie dnia (2-3 zdania) - ogólny ton rynku
2. Top 3 najważniejsze spostrzeżenia (konkretne liczby i trendy)
3. 2-3 rekomendacje działań dla biznesu (nie tylko bierz pod uwagi pogody, ale tylko ogolne trendy rynkowe i kryptowaluty)

ODPOWIEDZ W FORMACIE JSON (tylko JSON, bez dodatkowego tekstu):
{{
  "summary": "...",
  "insights": ["...", "...", "..."],
  "recommendations": ["...", "..."]
}}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        content = response.choices[0].message.content
        text = content.strip() if content else ""
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        result["generated_at"] = datetime.now().isoformat()
        return result
    except Exception as e:
        print(f"Błąd generowania AI insights: {e}")
        return {
            "summary": "Brak dostępnych insightów AI",
            "insights": [],
            "recommendations": [],
            "error": str(e),
        }


def analyze_trend(data_points: List[Dict], metric_name: str) -> str:
    """Bez zmian względem oryginału, ale z obsługą None."""
    if not data_points or len(data_points) < 2:
        return "Insufficient data for trend analysis"

    prompt = f"""Przeanalizuj trend dla metryki: {metric_name}

Dane (chronologicznie):
{json.dumps(data_points, indent=2)}

Opisz:
1. Jaki jest trend (wzrostowy/spadkowy/stabilny)?
2. O ile procent zmienił się w tym okresie?
3. Czy są zauważalne anomalie lub spike'i?

Odpowiedź w 2-3 zdaniach, konkretnie i liczbowo."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        content = response.choices[0].message.content
        return content.strip() if content else "No content returned."
    except Exception as e:
        return f"Trend analysis error: {str(e)}"


def explain_anomaly(anomaly_data: Dict) -> str:
    prompt = f"""Wykryto anomalię w danych:

{json.dumps(anomaly_data, indent=2)}

Wyjaśnij krótko (2-3 zdania):
1. Co mogło spowodować tę anomalię?
2. Czy to powód do niepokoju?
3. Jakie są możliwe następstwa?"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        content = response.choices[0].message.content
        return content.strip() if content else "No explanation received."
    except Exception as e:
        return f"Unable to explain anomaly: {str(e)}"