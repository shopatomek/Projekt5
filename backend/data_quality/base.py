
# WYJAŚNIENIE: To jest "umowa" (kontrakt) którą musi spełnić każdy check.
# ABC = Abstract Base Class. Nie można jej użyć bezpośrednio — tylko dziedziczyć.
# Każda klasa która dziedziczy po DataQualityCheck MUSI zaimplementować:
#   - validate() → czy rekord jest poprawny?
#   - fix()      → spróbuj naprawić rekord automatycznie
#

from abc import ABC, abstractmethod
from typing import Any, Dict


class DataQualityCheck(ABC):
    """
    Abstrakcyjna klasa bazowa dla pojedynczej reguły walidacji.
    Każdy check to osobna klasa z własną logiką validate() i fix().
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nazwa chceku — używana w raportach i logach. Np. 'RangeCheck:price_usd'"""

    @abstractmethod
    def validate(self, record: Dict[str, Any]) -> bool:
        """
        Sprawdza czy rekord spełnia regułę.
        Zwraca True jeśli OK, False jeśli błąd.
        NIE rzuca wyjątku — zawsze zwraca bool.
        """

    @abstractmethod
    def fix(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Próbuje naprawić błędny rekord.
        Zwraca rekord (zmodyfikowany lub nie).
        Domyślna implementacja: zwróć bez zmian (nie wszystko da się naprawić automatycznie).
        """
        return record