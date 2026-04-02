
# WYJAŚNIENIE: Reporter to obiekt który "odbiera" wynik walidacji i coś z nim robi.
#
# DWA REPORTERY:
# 1. LogReporter → wypisuje do stdout (docker logs) — zawsze aktywny
# 2. DatabaseReporter → zapisuje do tabeli ai_insights — aktywny gdy są błędy
#
# STRUKTURA REKORDU W ai_insights:
# {
#   "insight_type": "dq_failure",
#   "content": {
#     "table": "crypto_prices",
#     "record_id": "BTC",
#     "failed_checks": ["RangeCheck:price_change_24h[−100,100]"],
#     "original_record": {...},
#     "auto_repaired": false,
#     "checked_at": "2026-04-02T14:12:00Z"
#   },
#   "generated_at": "2026-04-02T14:12:00Z"
# }
#



import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("data_quality.reporters")


class LogReporter:
    """
    Zapisuje wyniki DQ do stdout (logi Dockera).
    Loguje TYLKO błędy — pomyślne walidacje są ciche (żeby nie zaśmiecać logów).

    Żeby zobaczyć logi DQ:
        docker logs dashboard-backend | grep "DQ"
        docker logs dashboard-backend | grep "⚠️"
    """

    def report(self, dq_report) -> None:
        if not dq_report.passed:
            logger.warning(
                f"DQ FAILURE | table={dq_report.table} "
                f"record={dq_report.record_id} "
                f"failed={dq_report.failed_checks} "
                f"repaired={dq_report.auto_repaired}"
            )


class DatabaseReporter:
    """
    Zapisuje błędy DQ do tabeli ai_insights w PostgreSQL.

    KIEDY ZAPISUJE: tylko gdy report.passed == False
    DLACZEGO: przy 2880 rekordach crypto/dzień zapisywanie wszystkich "OK"
              wypełniłoby bazę bezużytecznymi danymi. Zapisujemy tylko anomalie.

    UWAGA: execute_query jest importowane leniwie (lazy import) żeby uniknąć
    circular import — database.py zależy od innych modułów które mogą zależeć od DQ.
    """

    def report(self, dq_report) -> None:
        if dq_report.passed:
            return  # nie zapisujemy sukcesów

        # Lazy import żeby uniknąć circular import przy starcie aplikacji
        from database import execute_query

        # Budujemy content — JSONB w bazie
        content = {
            "table": dq_report.table,
            "record_id": dq_report.record_id,
            "failed_checks": dq_report.failed_checks,
            "total_checks": dq_report.total_checks,
            "auto_repaired": dq_report.auto_repaired,
            "checked_at": dq_report.checked_at,
            # Przechowujemy uproszczone wersje rekordów (bez dużych pól jak embeddings)
            "original_record": _safe_record(dq_report.original_record),
            "fixed_record": _safe_record(dq_report.fixed_record) if dq_report.auto_repaired else None,
        }

        try:
            execute_query(
                """
                INSERT INTO ai_insights (insight_type, content, generated_at)
                VALUES ('dq_failure', :content::jsonb, :ts)
                """,
                {
                    "content": json.dumps(content, default=str),
                    "ts": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as e:
            # Nie rzucamy — reporter nie powinien crashować głównego przepływu
            logger.error(f"DatabaseReporter: nie udało się zapisać do ai_insights: {e}")


def _safe_record(record: dict) -> dict:
    """
    Przygotowuje rekord do zapisu w JSON.
    Usuwa pole 'embedding' jeśli istnieje (byłoby 384 liczb — niepotrzebne w DQ logu).
    Konwertuje typy nie-serializable.
    """
    safe = {}
    for k, v in record.items():
        if k == "embedding":
            safe[k] = f"<vector {len(v)} dims>" if v else None
            continue
        try:
            json.dumps(v)  # sprawdź czy serializable
            safe[k] = v
        except (TypeError, ValueError):
            safe[k] = str(v)
    return safe