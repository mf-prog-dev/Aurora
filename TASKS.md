# Fairbanks Aurora Chaser Tasks

## In Progress

- [ ] Tune conservative thresholds after seeing live source behavior.

## Next

- [ ] Add a threshold tuning view that shows component scores side by side.
- [ ] Add a compact "why not Go" summary in the main row.

## Done

- [x] Move old prototype scripts and generated reports into ignored `legacy/`.
- [x] Scaffold a local-only Fairbanks aurora chasing application.
- [x] Define timezone-safe Fairbanks aurora night windows.
- [x] Implement conservative Go / Watch / Skip scoring.
- [x] Build a local dashboard for the next several Fairbanks nights.
- [x] Add focused tests for time windows and scoring gates.
- [x] Document local setup and run commands.
- [x] Add data source clients with timeouts and cache-friendly normalized records.
- [x] Verify the local dashboard and source fetch behavior.
- [x] Improve seasonal messaging when Fairbanks has no astronomical darkness.
- [x] Add richer night-detail timeline rows.
- [x] Add explicit UTC Kp source block visibility in the detail view.
- [x] Add manual refresh that bypasses the local cache.
- [x] Adjust Fairbanks scoring so Kp 4 is meaningful.
- [x] Add a clearer explanation of how Kp 4 differs for Fairbanks versus lower latitudes.
- [x] Track source coverage separately from source failure.

## Principles

- Use UTC internally for all comparisons, cache keys, and source timestamps.
- Present chasing nights in Fairbanks local time: `America/Anchorage`.
- Keep recommendations conservative; `Go` should be rare.
- Do not include flight or lodging logic in v1.
- Never store secrets in source files.
