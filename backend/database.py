import os
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Pobieranie danych połączenia
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")

# Dodajemy +psycopg2 dla jasności sterownika
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Inicjalizacja silnika
engine = create_engine(DATABASE_URL)


def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Wykonuje zapytanie SQL. Używa transakcji (autocommit).
    Zwraca listę słowników dla SELECT lub None dla innych operacji.
    """
    try:
        # engine.begin() automatycznie robi commit na końcu bloku 'with'
        with engine.begin() as connection:
            result = connection.execute(text(query), params or {})

            if result.returns_rows:
                # Konwersja rzędów na słowniki w sposób czytelny dla lintera
                return [dict(row._mapping) for row in result]

            return None
    except SQLAlchemyError as e:
        print(f"Baza danych - błąd krytyczny: {e}")
        raise e
