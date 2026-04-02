
#
# WYJAŚNIENIE: Silnik który łączy wszystko razem.
# Singleton — jeden engine dla całej aplikacji
#
# PRZEPŁYW DANYCH:
#
#   1. scheduler.py pobiera dane z Binance
#   2. Wywołuje: engine.run("crypto_prices", {"symbol": "BTC", "price_usd": 71000, ...})
#   3. Engine uruchamia wszystkie checks dla tej tabeli po kolei
#   4. Zbiera wyniki do DQReport
#   5. Próbuje fix() na błędnych polach
#   6. Przekazuje DQReport do Reporterów (LogReporter + DatabaseReporter)
#   7. Zwraca naprawiony rekord (lub oryginalny jeśli naprawa niemożliwa)
#
# DQReport to "zapis zdarzenia" — co sprawdzano, co się nie powiodło, czy naprawiono.
# Każdy DQReport trafia do tabeli ai_insights w bazie → Metabase może to pokazać.
#
# SŁOWNIK CHECKÓW:
# CHECKS_BY_TABLE = {
#   "crypto_prices": [check1, check2, check3],
#   "weather_data": [check1, check2],
#   ...
# }
# Żeby dodać nową tabelę: dodaj klucz do słownika. Nic innego się nie zmienia.

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import DataQualityCheck
from .checks import (
    NotNullCheck,
    RangeCheck,
    SentimentRangeCheck,
    UrlFormatCheck,
)

# Konfiguracja logowania — logi idą do stdout (Docker zbiera je przez `docker logs`)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DQ] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("data_quality")


# =============================================================================
# SŁOWNIK REGUŁ — które checks używamy dla której tabeli
# =============================================================================
# Żeby dodać nową tabelę → dodaj klucz i listę checków.
# Żeby dodać nową regułę do istniejącej tabeli → dodaj element do listy.
# Nic poza tym słownikiem się nie zmienia.

CHECKS_BY_TABLE: Dict[str, List[DataQualityCheck]] = {
    "crypto_prices": [
        NotNullCheck("symbol"),
        RangeCheck("price_usd", min_val=0.0, exclusive_min=True),   # cena musi być > 0
        RangeCheck("volume_24h", min_val=0.0),                       # wolumen >= 0
        RangeCheck("price_change_24h", min_val=-100.0, max_val=100.0),  # zmiana ±100%
    ],
    "weather_data": [
        NotNullCheck("city"),
        RangeCheck("temperature", min_val=-50.0, max_val=50.0),     # realistyczny zakres
        RangeCheck("humidity", min_val=0.0, max_val=100.0),         # procenty 0-100
        NotNullCheck("weather_condition"),
    ],
    "news_articles": [
        NotNullCheck("title"),
        NotNullCheck("source"),
        UrlFormatCheck("url"),
        NotNullCheck("published_at"),
        SentimentRangeCheck(),   # nullable: NULL jest OK gdy Groq nie działał
    ],
}


# =============================================================================
# DQReport — struktura danych opisująca wynik jednej walidacji
# =============================================================================

@dataclass
class DQReport:
    """
    Wynik walidacji jednego rekordu.
    Zapisywany do ai_insights.content jako JSONB.
    """
    table: str                          # "crypto_prices", "weather_data", "news_articles"
    passed: bool                        # True = wszystko OK
    failed_checks: List[str]            # nazwy checków które nie przeszły
    original_record: Dict[str, Any]     # oryginalny rekord PRZED fix()
    fixed_record: Dict[str, Any]        # rekord PO fix() (może być taki sam)
    auto_repaired: bool                 # czy fix() cokolwiek zmienił
    checked_at: str                     # ISO timestamp
    record_id: Optional[str] = None     # np. symbol dla crypto, city dla weather

    # Pomocnicze pole — liczba sprawdzonych pól
    total_checks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def summary_line(self) -> str:
        """Krótki opis do logów."""
        if self.passed:
            return f"✅ {self.table} [{self.record_id}] — wszystkie {self.total_checks} checks OK"
        status = "🔧 naprawiono" if self.auto_repaired else "❌ nie naprawiono"
        return (
            f"⚠️  {self.table} [{self.record_id}] — "
            f"FAILED: {self.failed_checks} ({status})"
        )


# =============================================================================
# DataQualityEngine — główny silnik
# =============================================================================

class DataQualityEngine:
    """
    Główny silnik DQ. Używany przez scheduler.py i app.py.

    Przykład użycia w scheduler.py:
        from data_quality.engine import engine  # singleton

        record = {"symbol": "BTC", "price_usd": 71000.0, ...}
        report, clean_record = engine.run("crypto_prices", record)
        # clean_record to naprawiony rekord (lub oryginalny jeśli naprawa niemożliwa)
    """

    def __init__(self, reporters=None):
        # reporters są wstrzykiwane — nie tworzymy ich tutaj żeby uniknąć circular import
        # Inicjalizacja następuje w __init__.py po zaimportowaniu wszystkich modułów
        self._reporters = reporters or []

    def set_reporters(self, reporters):
        self._reporters = reporters

    def run(
        self,
        table: str,
        record: Dict[str, Any],
        record_id: Optional[str] = None,
    ) -> tuple[DQReport, Dict[str, Any]]:
        """
        Uruchamia wszystkie checks dla danej tabeli.

        Zwraca:
            (DQReport, naprawiony_rekord)

        Przykład:
            report, clean = engine.run("crypto_prices", raw_record, record_id="BTC")
            if not report.passed:
                logger.warning(report.summary_line())
        """
        checks = CHECKS_BY_TABLE.get(table, [])
        if not checks:
            logger.debug(f"Brak checków dla tabeli: {table}")
            # Brak checków → zwróć pusty raport "passed"
            report = DQReport(
                table=table,
                passed=True,
                failed_checks=[],
                original_record=record,
                fixed_record=record,
                auto_repaired=False,
                checked_at=datetime.now(timezone.utc).isoformat(),
                record_id=record_id,
                total_checks=0,
            )
            return report, record

        original = dict(record)  # zachowaj kopię przed jakimikolwiek zmianami
        current = dict(record)   # aktualny stan — będziemy go modyfikować przez fix()
        failed_checks = []

        for check in checks:
            try:
                if not check.validate(current):
                    failed_checks.append(check.name)
                    # Próbuj naprawić — fix() zawsze zwraca rekord (zmodyfikowany lub nie)
                    current = check.fix(current)
                    logger.debug(f"  check FAILED: {check.name}, fix applied")
            except Exception as e:
                # Check sam wyrzucił wyjątek — traktujemy jako FAILED + logujemy
                logger.error(f"Check {check.name} wyrzucił wyjątek: {e}")
                failed_checks.append(f"{check.name}[ERROR]")

        auto_repaired = current != original and bool(failed_checks)
        passed = len(failed_checks) == 0

        report = DQReport(
            table=table,
            passed=passed,
            failed_checks=failed_checks,
            original_record=original,
            fixed_record=current,
            auto_repaired=auto_repaired,
            checked_at=datetime.now(timezone.utc).isoformat(),
            record_id=record_id,
            total_checks=len(checks),
        )

        # Loguj do stdout (zawsze)
        logger.info(report.summary_line())

        # Przekaż do wszystkich reporterów (DatabaseReporter zapisze do ai_insights)
        for reporter in self._reporters:
            try:
                reporter.report(report)
            except Exception as e:
                logger.error(f"Reporter {reporter.__class__.__name__} failed: {e}")

        return report, current

engine = DataQualityEngine()