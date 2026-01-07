# HomeOps v5 Foundation (pre-AI, pre-autofix)

This scaffold restructures the add-on to separate:
- API access (`app/ha_client.py`)
- Deterministic analysis (`app/health/*`)
- UI (`templates/`, `static/`)

## Pillars (v5 target)
1. State intelligence (normal vs abnormal)
2. Causal grouping (entities → devices → integrations)
3. Impact modeling (what breaks)
4. Actionable triage (ordered, safe)
5. Auditability & history (timeline of issues)
6. Export & sharing (support bundle, redaction)

## What is included now
- Deterministic Doctor report:
  - unavailable count + critical unavailable
  - unavailable by domain
  - pending updates
  - issue cards with safe “Start here” steps
- `/api/report` endpoint to fetch raw JSON (for later export/sharing)

## Next engineering steps (no AI)
- Add time-based context:
  - last_changed deltas for unavailable entities (recently working vs long-broken)
- Build integration clustering:
  - use device registry + entity registry via HA APIs (where available)
- Add automation dependency graph:
  - detect automations referencing unavailable entities
- Add report export:
  - Markdown “copy to reddit”
  - Redacted JSON bundle
