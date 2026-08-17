from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta

from .config import CONFIG, FAIRBANKS_TZ, UTC
from .models import AuroraNight, TimeWindow


def aware_local(value: date, hour: int) -> datetime:
    return datetime.combine(value, time(hour=hour), FAIRBANKS_TZ)


def build_aurora_nights(start_date: date | None = None, days: int | None = None) -> list[AuroraNight]:
    today = start_date or datetime.now(FAIRBANKS_TZ).date()
    count = days or CONFIG.forecast_days
    return [build_aurora_night(today + timedelta(days=i)) for i in range(count)]


def build_aurora_night(local_date: date) -> AuroraNight:
    start_local = aware_local(local_date, CONFIG.night_start_hour)
    end_local = aware_local(local_date + timedelta(days=1), CONFIG.night_end_hour)
    start_utc = start_local.astimezone(UTC)
    end_utc = end_local.astimezone(UTC)
    dark_windows = find_dark_windows(start_local, end_local)
    label = start_local.strftime("%a %b %-d")
    return AuroraNight(
        label=label,
        local_date=local_date.isoformat(),
        start_local=start_local,
        end_local=end_local,
        start_utc=start_utc,
        end_utc=end_utc,
        dark_windows_utc=tuple(dark_windows),
    )


def find_dark_windows(start_local: datetime, end_local: datetime) -> list[TimeWindow]:
    windows: list[TimeWindow] = []
    in_dark = False
    current_start: datetime | None = None
    cursor = start_local

    while cursor <= end_local:
        dark = solar_elevation_degrees(cursor, CONFIG.latitude, CONFIG.longitude) <= -18.0
        if dark and not in_dark:
            current_start = cursor
            in_dark = True
        if not dark and in_dark:
            windows.append(TimeWindow(current_start.astimezone(UTC), cursor.astimezone(UTC)))  # type: ignore[union-attr]
            current_start = None
            in_dark = False
        cursor += timedelta(minutes=30)

    if in_dark and current_start is not None:
        windows.append(TimeWindow(current_start.astimezone(UTC), end_local.astimezone(UTC)))

    return windows


def solar_elevation_degrees(moment: datetime, latitude: float, longitude: float) -> float:
    """Approximate solar elevation using NOAA's common solar-position equations."""
    local = moment.astimezone(FAIRBANKS_TZ)
    day_of_year = local.timetuple().tm_yday
    hour = local.hour + local.minute / 60 + local.second / 3600
    gamma = 2 * math.pi / 365 * (day_of_year - 1 + (hour - 12) / 24)

    declination = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )
    equation_of_time = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )

    offset_minutes = local.utcoffset().total_seconds() / 60 if local.utcoffset() else 0
    true_solar_time = (hour * 60 + equation_of_time + 4 * longitude - offset_minutes) % 1440
    hour_angle = math.radians(true_solar_time / 4 - 180)
    lat_rad = math.radians(latitude)
    elevation = math.asin(
        math.sin(lat_rad) * math.sin(declination)
        + math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle)
    )
    return math.degrees(elevation)


def moon_illumination_percent(local_date: date) -> float:
    """Approximate lunar illumination percentage; good enough for conservative gating."""
    known_new_moon = datetime(2000, 1, 6, 18, 14, tzinfo=UTC)
    noon_utc = datetime.combine(local_date, time(12), FAIRBANKS_TZ).astimezone(UTC)
    synodic_month_days = 29.53058867
    days = (noon_utc - known_new_moon).total_seconds() / 86400
    phase = (days % synodic_month_days) / synodic_month_days
    illumination = 100 * (1 - math.cos(2 * math.pi * phase)) / 2
    return round(illumination, 1)

