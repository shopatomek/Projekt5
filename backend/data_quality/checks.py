
# WYJAŚNIENIE: Konkretne implementacje reguł walidacji.
# Każda klasa to jedna reguła. Można je łączyć w dowolne kombinacje.
#
# JAK TO DZIAŁA:
# - NotNullCheck("title") → sprawdza czy pole "title" nie jest puste/None
# - RangeCheck("price_usd", min_val=0) → sprawdza czy cena > 0
# - RangeCheck("humidity", min_val=0, max_val=100) → sprawdza zakres
# - UrlFormatCheck("url") → sprawdza czy wygląda jak URL
#
# FIX(): Tam gdzie to możliwe, check próbuje naprawić dane.
# Np. jeśli sentiment_score wychodzi poza zakres [-1, 1] — przycinamy do granic.
# Jeśli cena jest 0 lub ujemna — nie da się naprawić, zwracamy rekord bez zmian.

from typing import Any, Dict, Optional
from .base import DataQualityCheck


class NotNullCheck(DataQualityCheck):
    """
    Sprawdza czy pole nie jest None, pustym stringiem, ani brakiem klucza.

    Przykład użycia:
        check = NotNullCheck("title")
        check.validate({"title": "Bitcoin rises"})  # → True
        check.validate({"title": ""})               # → False
        check.validate({"title": None})             # → False
        check.validate({})                          # → False
    """

    def __init__(self, field: str):
        self.field = field

    @property
    def name(self) -> str:
        return f"NotNullCheck:{self.field}"

    def validate(self, record: Dict[str, Any]) -> bool:
        value = record.get(self.field)
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        return True

    def fix(self, record: Dict[str, Any]) -> Dict[str, Any]:
        # Nie wiemy jaka powinna być poprawna wartość — nie naprawiamy
        # Logujemy tylko że wystąpił problem (engine to obsłuży)
        return record


class RangeCheck(DataQualityCheck):
    """
    Sprawdza czy wartość numeryczna mieści się w dopuszczalnym zakresie.
    Obsługuje: min_val, max_val, nullable (pole może być None — wtedy pomijamy check).

    Przykłady:
        RangeCheck("price_usd", min_val=0, exclusive_min=True)
            → price_usd musi być > 0 (nie >= 0)

        RangeCheck("humidity", min_val=0, max_val=100)
            → humidity musi być w [0, 100]

        RangeCheck("sentiment_score", min_val=-1.0, max_val=1.0, nullable=True)
            → jeśli None → OK, jeśli jest → musi być w [-1, 1]
    """

    def __init__(
        self,
        field: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        exclusive_min: bool = False,
        nullable: bool = False,
    ):
        self.field = field
        self.min_val = min_val
        self.max_val = max_val
        self.exclusive_min = exclusive_min
        self.nullable = nullable

    @property
    def name(self) -> str:
        return f"RangeCheck:{self.field}[{self.min_val},{self.max_val}]"

    def validate(self, record: Dict[str, Any]) -> bool:
        value = record.get(self.field)

        # Brak wartości
        if value is None:
            return self.nullable  # True jeśli nullable=True, False jeśli wymagane

        try:
            num = float(value)
        except (TypeError, ValueError):
            return False  # Nie jest liczbą → błąd

        if self.min_val is not None:
            if self.exclusive_min and num <= self.min_val:
                return False
            elif not self.exclusive_min and num < self.min_val:
                return False

        if self.max_val is not None and num > self.max_val:
            return False

        return True

    def fix(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dla zakresu możemy przyciąć wartość do granic — ale tylko dla niektórych pól.
        Np. sentiment_score=1.5 → przyciąć do 1.0 (ma sens)
        Ale price_usd=-100 → nie da się naprawić sensownie, zostawiamy
        """
        value = record.get(self.field)
        if value is None:
            return record

        try:
            num = float(value)
        except (TypeError, ValueError):
            return record

        fixed = num
        if self.max_val is not None and num > self.max_val:
            fixed = self.max_val
        if self.min_val is not None and num < self.min_val:
            fixed = self.min_val

        # Naprawiamy tylko jeśli to nie zmienia sensu biznesowego drastycznie
        # sentiment_score i humidity mają ograniczony zakres → naprawa OK
        # price_usd i price_change → nie naprawiamy (wartość byłaby bez sensu)
        REPAIRABLE_FIELDS = {"sentiment_score", "humidity"}
        if self.field in REPAIRABLE_FIELDS and fixed != num:
            record = dict(record)  # kopia żeby nie mutować oryginału
            record[self.field] = fixed

        return record


class UrlFormatCheck(DataQualityCheck):
    """
    Sprawdza czy pole wygląda jak URL (zaczyna się od http:// lub https://).
    Nie robi pełnej walidacji RFC — to wystarczy dla praktycznych celów.

    Przykład:
        check = UrlFormatCheck("url")
        check.validate({"url": "https://bbc.co.uk/news/123"})  # → True
        check.validate({"url": "not-a-url"})                   # → False
        check.validate({"url": ""})                            # → False
        check.validate({"url": None})                          # → False
    """

    def __init__(self, field: str):
        self.field = field

    @property
    def name(self) -> str:
        return f"UrlFormatCheck:{self.field}"

    def validate(self, record: Dict[str, Any]) -> bool:
        value = record.get(self.field)
        if not value or not isinstance(value, str):
            return False
        return value.strip().startswith(("http://", "https://"))

    def fix(self, record: Dict[str, Any]) -> Dict[str, Any]:
        # URL-a nie naprawiamy automatycznie — nie wiadomo jaki powinien być
        return record


