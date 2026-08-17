from __future__ import annotations

from datetime import datetime, timedelta

from .config import FAIRBANKS_TZ, UTC
from .models import AuroraNight, HourlyDetail, HourlyWeather, KpBlockDetail, KpRecord, NightAssessment
from .time_windows import moon_illumination_percent


def assess_night(
    night: AuroraNight,
    weather: list[HourlyWeather],
    kp_records: list[KpRecord],
    source_failures: list[str] | None = None,
    now_utc: datetime | None = None,
) -> NightAssessment:
    now = now_utc or datetime.now(UTC)
    failures = source_failures or []
    weather_in_dark = filter_weather_for_darkness(night, weather)
    kp_in_night = [record.kp for record in kp_records if night.start_utc <= record.time_utc < night.end_utc]
    kp_blocks = build_kp_block_details(night, kp_records)
    weather_in_night = [
        entry for entry in weather if night.start_utc <= entry.time_utc < night.end_utc
    ]
    kp_coverage = kp_coverage_for(night, kp_records, kp_blocks)
    weather_coverage = weather_coverage_for(weather, weather_in_night)
    clouds = [entry.cloud_cover for entry in weather_in_dark if entry.cloud_cover is not None]
    temps = [entry.temperature_f for entry in weather_in_dark if entry.temperature_f is not None]
    precip = [
        entry.precipitation_probability
        for entry in weather_in_dark
        if entry.precipitation_probability is not None
    ]

    max_kp = max(kp_in_night) if kp_in_night else None
    avg_cloud = round(sum(clouds) / len(clouds), 1) if clouds else None
    min_cloud = min(clouds) if clouds else None
    moon = moon_illumination_percent(night.start_local.date())
    days_out = max(0.0, (night.start_utc - now).total_seconds() / 86400)

    aurora_score = score_aurora(max_kp)
    sky_score = score_sky(avg_cloud)
    darkness_score = score_darkness(night.dark_hours)
    moon_score = score_moon(moon, max_kp)
    comfort_score = score_comfort(temps, precip)
    confidence = confidence_label(days_out, failures)

    raw_score = (
        aurora_score * 0.4
        + sky_score * 0.35
        + darkness_score * 0.1
        + moon_score * 0.1
        + comfort_score * 0.05
    )
    score = int(round(raw_score))
    blockers = blockers_for(night, max_kp, avg_cloud, moon, days_out, failures, kp_coverage, weather_coverage)
    recommendation = recommendation_for(score, blockers)
    reasons = reasons_for(max_kp, avg_cloud, moon, night.dark_hours, confidence, kp_coverage, weather_coverage)
    seasonal_note = seasonal_note_for(night)
    hourly_details = build_hourly_details(night, weather, kp_records)

    return NightAssessment(
        night=night,
        recommendation=recommendation,
        score=score,
        confidence=confidence,
        aurora_score=aurora_score,
        sky_score=sky_score,
        darkness_score=darkness_score,
        moon_score=moon_score,
        comfort_score=comfort_score,
        max_kp=max_kp,
        avg_cloud_cover=avg_cloud,
        min_cloud_cover=min_cloud,
        moon_illumination=moon,
        kp_coverage=kp_coverage,
        weather_coverage=weather_coverage,
        kp_blocks=kp_blocks,
        seasonal_note=seasonal_note,
        hourly_details=hourly_details,
        blockers=blockers,
        reasons=reasons,
    )


def filter_weather_for_darkness(night: AuroraNight, weather: list[HourlyWeather]) -> list[HourlyWeather]:
    if not night.dark_windows_utc:
        return [entry for entry in weather if night.start_utc <= entry.time_utc < night.end_utc]
    return [
        entry
        for entry in weather
        if any(window.contains(entry.time_utc) for window in night.dark_windows_utc)
    ]


def build_hourly_details(
    night: AuroraNight,
    weather: list[HourlyWeather],
    kp_records: list[KpRecord],
) -> list[HourlyDetail]:
    rows: list[HourlyDetail] = []
    weather_in_night = [
        entry for entry in weather if night.start_utc <= entry.time_utc < night.end_utc
    ]
    for entry in weather_in_night:
        local = entry.time_utc.astimezone(FAIRBANKS_TZ)
        rows.append(
            HourlyDetail(
                time_utc=entry.time_utc,
                time_local_label=local.strftime("%a %-I %p"),
                is_dark=any(window.contains(entry.time_utc) for window in night.dark_windows_utc),
                kp=kp_for_hour(entry.time_utc, kp_records),
                cloud_cover=entry.cloud_cover,
                precipitation_probability=entry.precipitation_probability,
                temperature_f=entry.temperature_f,
            )
        )
    return rows


def kp_for_hour(moment_utc: datetime, kp_records: list[KpRecord]) -> float | None:
    matching = [
        record
        for record in kp_records
        if record.time_utc <= moment_utc < record.time_utc + timedelta(hours=3)
    ]
    if matching:
        return matching[-1].kp

    prior = [record for record in kp_records if record.time_utc <= moment_utc]
    if not prior:
        return None
    latest = max(prior, key=lambda record: record.time_utc)
    age_hours = (moment_utc - latest.time_utc).total_seconds() / 3600
    if age_hours <= 3:
        return latest.kp
    return None


def build_kp_block_details(night: AuroraNight, kp_records: list[KpRecord]) -> list[KpBlockDetail]:
    blocks: list[KpBlockDetail] = []
    for record in kp_records:
        start_utc = record.time_utc
        end_utc = record.time_utc + timedelta(hours=3)
        if end_utc <= night.start_utc or start_utc >= night.end_utc:
            continue
        start_local = start_utc.astimezone(FAIRBANKS_TZ)
        end_local = end_utc.astimezone(FAIRBANKS_TZ)
        blocks.append(
            KpBlockDetail(
                start_utc=start_utc,
                end_utc=end_utc,
                utc_label=f"{start_utc.strftime('%b %-d %H:%M')} to {end_utc.strftime('%H:%M')} UTC",
                fairbanks_label=f"{start_local.strftime('%b %-d %-I %p')} to {end_local.strftime('%-I %p')} AK",
                kp=record.kp,
                source=record.source,
            )
        )
    return blocks


def kp_coverage_for(
    night: AuroraNight,
    kp_records: list[KpRecord],
    kp_blocks: list[KpBlockDetail],
) -> str:
    if kp_blocks:
        return "covered"
    if not kp_records:
        return "missing"
    latest_end = max(record.time_utc + timedelta(hours=3) for record in kp_records)
    earliest_start = min(record.time_utc for record in kp_records)
    if night.start_utc >= latest_end:
        return "forecast does not extend this far"
    if night.end_utc <= earliest_start:
        return "before available forecast"
    return "gap"


def weather_coverage_for(weather: list[HourlyWeather], weather_in_night: list[HourlyWeather]) -> str:
    if weather_in_night:
        return "covered"
    if not weather:
        return "missing"
    return "forecast does not cover this night"


def score_aurora(max_kp: float | None) -> int:
    if max_kp is None:
        return 0
    if max_kp >= 7:
        return 100
    if max_kp >= 6:
        return 90
    if max_kp >= 5:
        return 72
    if max_kp >= 4:
        return 62
    if max_kp >= 3:
        return 28
    return 10


def score_sky(avg_cloud: float | None) -> int:
    if avg_cloud is None:
        return 0
    if avg_cloud <= 15:
        return 100
    if avg_cloud <= 30:
        return 85
    if avg_cloud <= 50:
        return 55
    if avg_cloud <= 70:
        return 25
    return 0


def score_darkness(dark_hours: float) -> int:
    if dark_hours >= 6:
        return 100
    if dark_hours >= 4:
        return 80
    if dark_hours >= 2:
        return 45
    if dark_hours > 0:
        return 20
    return 0


def score_moon(moon: float, max_kp: float | None) -> int:
    if moon <= 20:
        return 100
    if moon <= 50:
        return 70
    if moon <= 80:
        return 35 if (max_kp or 0) < 7 else 55
    return 15 if (max_kp or 0) < 7 else 40


def score_comfort(temps: list[float], precip: list[float]) -> int:
    temp_score = 70
    if temps:
        avg_temp = sum(temps) / len(temps)
        if avg_temp < -20:
            temp_score = 25
        elif avg_temp < 0:
            temp_score = 50
        elif avg_temp <= 35:
            temp_score = 85
        else:
            temp_score = 75
    precip_score = 70
    if precip:
        avg_precip = sum(precip) / len(precip)
        if avg_precip <= 10:
            precip_score = 100
        elif avg_precip <= 35:
            precip_score = 65
        else:
            precip_score = 25
    return int(round((temp_score + precip_score) / 2))


def blockers_for(
    night: AuroraNight,
    max_kp: float | None,
    avg_cloud: float | None,
    moon: float,
    days_out: float,
    source_failures: list[str],
    kp_coverage: str,
    weather_coverage: str,
) -> list[str]:
    blockers: list[str] = []
    if source_failures:
        blockers.append("Required source data is missing.")
    if not night.has_astronomical_darkness:
        blockers.append("No astronomical darkness in the chasing window.")
    if max_kp is None:
        blockers.append(f"Kp coverage: {kp_coverage}.")
    elif max_kp < 4:
        blockers.append("Kp signal is below the Fairbanks conservative Go threshold.")
    if avg_cloud is None:
        blockers.append(f"Weather coverage: {weather_coverage}.")
    elif avg_cloud > 70:
        blockers.append("Cloud cover is too high for a Go recommendation.")
    if moon > 80 and (max_kp or 0) < 7:
        blockers.append("Moonlight is very bright without an exceptional Kp signal.")
    if days_out > 4:
        blockers.append("Forecast is too far out for a Go recommendation.")
    return blockers


def seasonal_note_for(night: AuroraNight) -> str | None:
    if night.has_astronomical_darkness:
        return None
    return (
        "Fairbanks has no astronomical darkness during this chasing window. "
        "Treat aurora chasing as out of season until dark hours return."
    )


def recommendation_for(score: int, blockers: list[str]) -> str:
    if any("No astronomical darkness" in blocker for blocker in blockers):
        return "Skip"
    if score >= 80 and not blockers:
        return "Go"
    if score >= 55:
        return "Watch"
    return "Skip"


def confidence_label(days_out: float, source_failures: list[str]) -> str:
    if source_failures:
        return "Low"
    if days_out <= 2:
        return "High"
    if days_out <= 4:
        return "Medium"
    return "Low"


def reasons_for(
    max_kp: float | None,
    avg_cloud: float | None,
    moon: float,
    dark_hours: float,
    confidence: str,
    kp_coverage: str,
    weather_coverage: str,
) -> list[str]:
    return [
        f"Max Kp: {max_kp:.1f}" if max_kp is not None else "Max Kp: unavailable",
        f"Kp coverage: {kp_coverage}",
        f"Average cloud cover during darkness: {avg_cloud:.0f}%" if avg_cloud is not None else "Cloud cover: unavailable",
        f"Weather coverage: {weather_coverage}",
        f"Moon illumination: {moon:.0f}%",
        f"Astronomical darkness: {dark_hours:.1f} hours",
        f"Forecast confidence: {confidence}",
    ]
