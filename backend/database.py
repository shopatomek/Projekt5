import os
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Pobieranie danych połączenia z Twojego .env
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")

# URL połączenia
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Inicjalizacja silnika
# pool_pre_ping=True sprawdza połączenie przed każdym zapytaniem (zapobiega błędom "Connection lost")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Uniwersalna funkcja do zapytań SQL.
    Automatycznie zarządza transakcjami (commit/rollback) dzięki engine.begin().
    """
    try:
        with engine.begin() as connection:
            result = connection.execute(text(query), params or {})

            if result.returns_rows:
                # Mapowanie rzędów na słowniki dla łatwego użycia w JSON (FastAPI)
                return [dict(row._mapping) for row in result]

            return None
    except SQLAlchemyError as e:
        print(f"❌ Błąd SQLAlchemy przy zapytaniu: {query}")
        print(f"Szczegóły: {e}")
        raise e
