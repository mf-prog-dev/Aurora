from __future__ import annotations

from datetime import datetime

from .config import FAIRBANKS_TZ, UTC
from .data_sources import get_kp_records, get_weather
from .models import NightAssessment, SourceStatus
from .scoring import assess_night
from .time_windows import build_aurora_nights


def build_assessments(force_refresh: bool = False) -> tuple[list[NightAssessment], list[SourceStatus]]:
    weather, weather_status = get_weather(force_refresh=force_refresh)
    kp_records, kp_status = get_kp_records(force_refresh=force_refresh)
    statuses = [weather_status, kp_status]
    failures = [status.name for status in statuses if not status.ok]
    nights = build_aurora_nights()
    assessments = [
        assess_night(night, weather, kp_records, failures, datetime.now(UTC))
        for night in nights
    ]
    return assessments, statuses


def render_dashboard(
    assessments: list[NightAssessment],
    statuses: list[SourceStatus],
    force_refresh: bool = False,
) -> str:
    rows = "\n".join(render_row(assessment) for assessment in assessments)
    status_items = "\n".join(render_status(status) for status in statuses)
    generated = datetime.now(FAIRBANKS_TZ).strftime("%Y-%m-%d %H:%M %Z")
    refresh_note = "Manual refresh fetched fresh source data." if force_refresh else "Normal reload uses the local cache for about 60 minutes."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fairbanks Aurora Chaser</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8f5;
      --ink: #17201b;
      --muted: #5a655d;
      --line: #d8ded7;
      --go: #0f7b4f;
      --watch: #9a6700;
      --skip: #a33a32;
      --panel: #ffffff;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header, main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }}
    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 20px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 28px;
      letter-spacing: 0;
    }}
    p {{
      margin: 0;
      color: var(--muted);
    }}
    .refresh {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      padding: 10px 14px;
      border-radius: 6px;
      text-decoration: none;
      white-space: nowrap;
    }}
    .actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
    }}
    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
      background: #eef2ed;
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    .badge {{
      display: inline-block;
      min-width: 58px;
      padding: 4px 8px;
      border-radius: 5px;
      color: white;
      text-align: center;
      font-weight: 700;
    }}
    .Go {{ background: var(--go); }}
    .Watch {{ background: var(--watch); }}
    .Skip {{ background: var(--skip); }}
    details {{
      max-width: 520px;
    }}
    summary {{
      cursor: pointer;
      color: var(--ink);
    }}
    ul {{
      margin: 8px 0 0;
      padding-left: 18px;
      color: var(--muted);
    }}
    .note {{
      margin: 10px 0;
      padding: 10px;
      background: #fff7d6;
      border: 1px solid #e8d58a;
      border-radius: 6px;
      color: #51430f;
    }}
    .info {{
      margin: 14px 0;
      padding: 12px;
      background: #eaf5ef;
      border: 1px solid #b9d7c7;
      border-radius: 6px;
      color: #214638;
    }}
    .hourly {{
      margin-top: 12px;
      width: 100%;
      border: 1px solid var(--line);
      background: #fbfcfa;
    }}
    .hourly th, .hourly td {{
      padding: 6px 7px;
      font-size: 12px;
      white-space: nowrap;
    }}
    .dark-cell {{
      font-weight: 700;
      color: var(--go);
    }}
    .kp-blocks {{
      margin-top: 12px;
      width: 100%;
      border: 1px solid var(--line);
      background: #fbfcfa;
    }}
    .kp-blocks th, .kp-blocks td {{
      padding: 6px 7px;
      font-size: 12px;
    }}
    .sources {{
      margin-top: 20px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .source {{
      border: 1px solid var(--line);
      background: var(--panel);
      padding: 12px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Fairbanks Aurora Chaser</h1>
      <p>Conservative local outlook. Times are Fairbanks local; scoring uses UTC internally.</p>
    </div>
    <div class="actions">
      <a class="refresh" href="/">Reload</a>
      <a class="refresh" href="/?refresh=1">Fetch Fresh Data</a>
    </div>
  </header>
  <main>
    <p>Generated {generated}. {refresh_note}</p>
    <div class="info">Fairbanks sits under the auroral oval, so Kp 4 can be meaningful here. The app still requires clear skies, dark hours, near-term confidence, and manageable moonlight before it will say Go.</div>
    <table aria-label="Fairbanks aurora outlook">
      <thead>
        <tr>
          <th>Night</th>
          <th>Call</th>
          <th>Score</th>
          <th>Kp</th>
          <th>Clouds</th>
          <th>Moon</th>
          <th>Dark</th>
          <th>Confidence</th>
          <th>Why</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <section class="sources">
      {status_items}
    </section>
  </main>
</body>
</html>"""


def render_row(assessment: NightAssessment) -> str:
    night = assessment.night
    kp = f"{assessment.max_kp:.1f}" if assessment.max_kp is not None else "n/a"
    clouds = f"{assessment.avg_cloud_cover:.0f}%" if assessment.avg_cloud_cover is not None else "n/a"
    reasons = "".join(f"<li>{escape(reason)}</li>" for reason in assessment.reasons)
    blockers = "".join(f"<li>{escape(blocker)}</li>" for blocker in assessment.blockers)
    blocker_section = f"<strong>Go blockers</strong><ul>{blockers}</ul>" if blockers else "<strong>No Go blockers</strong>"
    seasonal_note = f'<div class="note">{escape(assessment.seasonal_note)}</div>' if assessment.seasonal_note else ""
    kp_blocks = render_kp_blocks(assessment)
    hourly = render_hourly_details(assessment)
    return f"""
<tr>
  <td><strong>{escape(night.label)}</strong><br>{night.start_local.strftime("%b %-d %H:%M")} to {night.end_local.strftime("%b %-d %H:%M")}</td>
  <td><span class="badge {assessment.recommendation}">{assessment.recommendation}</span></td>
  <td>{assessment.score}</td>
  <td>{kp}</td>
  <td>{clouds}</td>
  <td>{assessment.moon_illumination:.0f}%</td>
  <td>{night.dark_hours:.1f}h</td>
  <td>{assessment.confidence}</td>
  <td>
    <details>
      <summary>Details</summary>
      {seasonal_note}
      <ul>{reasons}</ul>
      {blocker_section}
      {kp_blocks}
      {hourly}
    </details>
  </td>
</tr>"""


def render_kp_blocks(assessment: NightAssessment) -> str:
    if not assessment.kp_blocks:
        return f'<p class="note">No NOAA Kp forecast blocks overlap this Fairbanks night. Coverage: {escape(assessment.kp_coverage)}.</p>'
    rows = "\n".join(
        f"""<tr>
  <td>{escape(block.utc_label)}</td>
  <td>{escape(block.fairbanks_label)}</td>
  <td>{block.kp:.1f}</td>
  <td>{escape(block.source)}</td>
</tr>"""
        for block in assessment.kp_blocks
    )
    return f"""<table class="kp-blocks" aria-label="Kp blocks for {escape(assessment.night.label)}">
  <thead>
    <tr>
      <th>UTC Kp Block</th>
      <th>Fairbanks Time</th>
      <th>Kp</th>
      <th>Source</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>"""


def render_hourly_details(assessment: NightAssessment) -> str:
    if not assessment.hourly_details:
        return '<p class="note">No hourly weather rows are available for this night.</p>'
    rows = "\n".join(
        f"""<tr>
  <td>{escape(detail.time_local_label)}</td>
  <td class="{'dark-cell' if detail.is_dark else ''}">{'dark' if detail.is_dark else 'dim'}</td>
  <td>{format_number(detail.kp, 1)}</td>
  <td>{format_percent(detail.cloud_cover)}</td>
  <td>{format_percent(detail.precipitation_probability)}</td>
  <td>{format_number(detail.temperature_f, 0)}&deg;F</td>
</tr>"""
        for detail in assessment.hourly_details
    )
    return f"""<table class="hourly" aria-label="Hourly detail for {escape(assessment.night.label)}">
  <thead>
    <tr>
      <th>Time</th>
      <th>Sky</th>
      <th>Kp</th>
      <th>Cloud</th>
      <th>Precip</th>
      <th>Temp</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>"""


def render_status(status: SourceStatus) -> str:
    state = "OK" if status.ok else "Issue"
    fetched = status.fetched_at_utc.astimezone(FAIRBANKS_TZ).strftime("%Y-%m-%d %H:%M %Z") if status.fetched_at_utc else "n/a"
    return f"""<div class="source">
  <strong>{escape(status.name)}</strong><br>
  {state}: {escape(status.message)}<br>
  Last checked: {escape(fetched)}
</div>"""


def escape(value: str) -> str:
    if value is None:
        return ""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.0f}%"


def format_number(value: float | None, digits: int) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"
