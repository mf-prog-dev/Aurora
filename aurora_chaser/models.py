from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TimeWindow:
    start_utc: datetime
    end_utc: datetime

    def contains(self, value: datetime) -> bool:
        return self.start_utc <= value < self.end_utc


@dataclass(frozen=True)
class AuroraNight:
    label: str
    local_date: str
    start_local: datetime
    end_local: datetime
    start_utc: datetime
    end_utc: datetime
    dark_windows_utc: tuple[TimeWindow, ...]

    @property
    def has_astronomical_darkness(self) -> bool:
        return bool(self.dark_windows_utc)

    @property
    def dark_hours(self) -> float:
        total_seconds = sum(
            (window.end_utc - window.start_utc).total_seconds()
            for window in self.dark_windows_utc
        )
        return round(total_seconds / 3600, 1)


@dataclass(frozen=True)
class HourlyWeather:
    time_utc: datetime
    cloud_cover: float | None
    precipitation_probability: float | None
    temperature_f: float | None


@dataclass(frozen=True)
class KpRecord:
    time_utc: datetime
    kp: float
    source: str


@dataclass(frozen=True)
class KpBlockDetail:
    start_utc: datetime
    end_utc: datetime
    utc_label: str
    fairbanks_label: str
    kp: float
    source: str


@dataclass(frozen=True)
class HourlyDetail:
    time_utc: datetime
    time_local_label: str
    is_dark: bool
    kp: float | None
    cloud_cover: float | None
    precipitation_probability: float | None
    temperature_f: float | None


@dataclass
class SourceStatus:
    name: str
    ok: bool
    message: str
    fetched_at_utc: datetime | None = None


@dataclass
class NightAssessment:
    night: AuroraNight
    recommendation: str
    score: int
    confidence: str
    aurora_score: int
    sky_score: int
    darkness_score: int
    moon_score: int
    comfort_score: int
    max_kp: float | None
    avg_cloud_cover: float | None
    min_cloud_cover: float | None
    moon_illumination: float
    kp_blocks: list[KpBlockDetail] = field(default_factory=list)
    seasonal_note: str | None = None
    hourly_details: list[HourlyDetail] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
