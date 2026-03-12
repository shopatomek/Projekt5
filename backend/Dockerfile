# Używamy lekkiego obrazu Pythona
FROM python:3.11-slim

# Ustawiamy katalog roboczy wewnątrz kontenera
WORKDIR /app

# Kopiujemy listę zależności i instalujemy je
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę kodu aplikacji
COPY . .

# Wystawiamy port, na którym działa FastAPI
EXPOSE 8000

# Komenda startowa (zostanie i tak nadpisana przez docker-compose, ale warto ją mieć)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]