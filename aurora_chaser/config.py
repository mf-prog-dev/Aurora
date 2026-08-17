from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo


UTC = ZoneInfo("UTC")
FAIRBANKS_TZ = ZoneInfo("America/Anchorage")


@dataclass(frozen=True)
class AppConfig:
    location_name: str = "Fairbanks, Alaska"
    latitude: float = 64.8378
    longitude: float = -147.7164
    night_start_hour: int = 18
    night_end_hour: int = 8
    forecast_days: int = 7
    request_timeout_seconds: int = 15
    cache_ttl_minutes: int = 60


CONFIG = AppConfig()

