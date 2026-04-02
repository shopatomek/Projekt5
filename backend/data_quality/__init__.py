from .engine import engine, DQReport
from .reporters import DatabaseReporter, LogReporter
 
# LogReporter → zawsze aktywny (logi stdout)
# DatabaseReporter → zapisuje błędy do ai_insights
engine.set_reporters([
    LogReporter(),
    DatabaseReporter(),
])
 
__all__ = ["engine", "DQReport"]