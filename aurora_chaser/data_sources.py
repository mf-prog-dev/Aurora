from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import CONFIG, UTC
from .models import HourlyWeather, KpRecord, SourceStatus


DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "aurora.sqlite3"


def init_cache() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    fetched_at_utc TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )


def cached_json(key: str, fetcher, force_refresh: bool = False) -> tuple[object | None, SourceStatus]:
    init_cache()
    now = datetime.now(UTC)
    if not force_refresh:
        with closing(sqlite3.connect(DB_PATH)) as db:
            row = db.execute("SELECT fetched_at_utc, payload FROM cache WHERE key = ?", (key,)).fetchone()
            if row:
                fetched_at = datetime.fromisoformat(row[0])
                if now - fetched_at < timedelta(minutes=CONFIG.cache_ttl_minutes):
                    return json.loads(row[1]), SourceStatus(key, True, "Loaded from local cache.", fetched_at)

    try:
        payload = fetcher()
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return None, SourceStatus(key, False, f"Fetch failed: {exc}", now)

    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute(
                "REPLACE INTO cache (key, fetched_at_utc, payload) VALUES (?, ?, ?)",
                (key, now.isoformat(), json.dumps(payload)),
            )
    message = "Fetched live after manual refresh." if force_refresh else "Fetched live."
    return payload, SourceStatus(key, True, message, now)


def fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": "fairbanks-aurora-chaser/0.1"})
    with urlopen(request, timeout=CONFIG.request_timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def get_weather(force_refresh: bool = False) -> tuple[list[HourlyWeather], SourceStatus]:
    params = urlencode(
        {
            "latitude": CONFIG.latitude,
            "longitude": CONFIG.longitude,
            "hourly": "cloud_cover,precipitation_probability,temperature_2m",
            "temperature_unit": "fahrenheit",
            "timezone": "UTC",
            "forecast_days": CONFIG.forecast_days + 1,
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    payload, status = cached_json("weather", lambda: fetch_json(url), force_refresh)
    if not isinstance(payload, dict):
        return [], status

    hourly = payload.get("hourly", {})
    records: list[HourlyWeather] = []
    for index, raw_time in enumerate(hourly.get("time", [])):
        records.append(
            HourlyWeather(
                time_utc=parse_utc(raw_time),
                cloud_cover=value_at(hourly.get("cloud_cover"), index),
                precipitation_probability=value_at(hourly.get("precipitation_probability"), index),
                temperature_f=value_at(hourly.get("temperature_2m"), index),
            )
        )
    return records, status


def get_kp_records(force_refresh: bool = False) -> tuple[list[KpRecord], SourceStatus]:
    url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
    payload, status = cached_json("kp_forecast", lambda: fetch_json(url), force_refresh)
    records: list[KpRecord] = []
    if not isinstance(payload, list) or not payload:
        return records, status

    if isinstance(payload[0], dict):
        for row in payload:
            try:
                raw_time = row.get("time_tag") or row.get("time") or row.get("time_utc")
                raw_kp = row.get("kp") or row.get("estimated_kp") or row.get("kp_index")
                records.append(KpRecord(parse_utc(raw_time), float(raw_kp), "NOAA Kp forecast"))
            except (AttributeError, TypeError, ValueError):
                continue
        return records, status

    if len(payload) >= 2:
        headers = [str(value).lower() for value in payload[0]]
        time_index = find_header(headers, ("time_tag", "time", "utc"))
        kp_index = find_header(headers, ("kp", "estimated_kp", "kp_index"))
        if time_index is None or kp_index is None:
            return records, SourceStatus("kp_forecast", False, "Unexpected NOAA Kp format.", status.fetched_at_utc)

        for row in payload[1:]:
            try:
                records.append(KpRecord(parse_utc(row[time_index]), float(row[kp_index]), "NOAA Kp forecast"))
            except (TypeError, ValueError, IndexError):
                continue
    return records, status


def parse_utc(value: str | None) -> datetime:
    if value is None:
        raise ValueError("missing datetime")
    clean = value.replace("Z", "+00:00")
    if "T" not in clean and " " in clean:
        clean = clean.replace(" ", "T")
    parsed = datetime.fromisoformat(clean)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def value_at(values: list | None, index: int) -> float | None:
    if values is None or index >= len(values) or values[index] is None:
        return None
    return float(values[index])


def find_header(headers: list[str], candidates: tuple[str, ...]) -> int | None:
    for candidate in candidates:
        for index, header in enumerate(headers):
            if candidate in header:
                return index
    return None
