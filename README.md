# Fairbanks Aurora Chaser

A local-only, conservative aurora chasing dashboard for Fairbanks, Alaska.

The app uses UTC internally for forecast matching and cache records, then displays aurora nights in Fairbanks local time (`America/Anchorage`). A night is modeled as evening through the following morning, not a calendar day.

## Run

```bash
python3 -m aurora_chaser.server
```

Open:

```text
http://127.0.0.1:8765
```

## Test

```bash
python3 -m unittest discover -s tests
```

## V1 Scope

- Fairbanks only
- Local app only
- No flight or lodging logic
- Conservative `Go / Watch / Skip` recommendations
- No secrets in source code

## Data Sources

- NOAA planetary K-index forecast
- Open-Meteo Fairbanks hourly weather forecast
- Local approximate moon illumination
- Local approximate astronomical darkness calculation
