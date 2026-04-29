# Używamy lekkiego obrazu Pythona
FROM python:3.11-slim

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy listę zależności i instalujemy je
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Kopiujemy resztę kodu aplikacji
COPY . .

# Wystawiamy port
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]