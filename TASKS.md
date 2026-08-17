# Fairbanks Aurora Chaser Tasks

## In Progress

- [ ] Tune conservative thresholds after seeing live source behavior.

## Next

- [ ] Add richer night-detail timeline rows.
- [ ] Consider a manual refresh/force-cache-clear control.
- [ ] Improve seasonal messaging when Fairbanks has no astronomical darkness.

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

## Principles

- Use UTC internally for all comparisons, cache keys, and source timestamps.
- Present chasing nights in Fairbanks local time: `America/Anchorage`.
- Keep recommendations conservative; `Go` should be rare.
- Do not include flight or lodging logic in v1.
- Never store secrets in source files.
