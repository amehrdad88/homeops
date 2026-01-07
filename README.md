# HomeOps (Add-on)

HomeOps is a local-first operational control plane for Home Assistant. This add-on currently ships a **read-only Doctor** UI that surfaces health signals (availability, updates) and explains impact deterministically (no AI, no autofix).

## Dev workflow (recommended)
1. Edit code locally.
2. Commit + push to GitHub.
3. In Home Assistant: Add-on Store → ⋮ → Check for updates → Update/Restart HomeOps.

## Structure
- `homeops/` — Home Assistant add-on
  - `app/` — Python application code (Flask)
  - `templates/` + `static/` — UI assets
  - `health/` — deterministic analysis engine (v5 foundation)
- `docs/` — product + engineering specs
