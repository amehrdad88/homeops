# HomeOps Project Plan (v0 → v1)

This document is designed to be copy/pasted into Notion.

## Mission
Make Home Assistant “just work” by providing:
1) **Doctor**: detect issues, explain them clearly, and suggest fixes.
2) **Safe Change Engine**: implement fixes with an approval step + rollback.

## North Star (first 14 days)
Ship a working add-on with Ingress that:
- connects to the HA Core API via Supervisor proxy
- shows a Doctor dashboard
- exports a diagnostics bundle
- supports one safe change end-to-end (a very small one)

---

## Phase 0 — Setup (DONE)
- [x] Home Assistant OS installed
- [x] SSH add-on installed
- [x] Samba add-on installed
- [x] Notion MCP connected
- [x] GitHub repo connected

## Phase 1 — “Hello HomeOps” Add-on (TODAY)
**Goal:** Add-on appears in the Add-on Store and opens a HomeOps UI in HA sidebar via Ingress.

Tasks:
- [ ] Create `repository.yaml` at repo root (required for add-on repo)
- [ ] Create add-on folder `homeops/` with:
  - `config.yaml`
  - `Dockerfile`
  - `run.sh`
  - `server.py`
- [ ] Install add-on from repo in Home Assistant
- [ ] Verify UI renders and `/api/doctor` returns HA info

Acceptance criteria:
- UI shows HA version + entity count
- No YAML required by user
- Diagnostics can be copied from UI

## Phase 2 — Doctor v0.1 (NEXT)
**Goal:** Useful diagnostics, not just “info”.

Tasks:
- [ ] Add “Connectivity checks” (Core API reachable, websocket reachable)
- [ ] Add “Integration health” checks (list failed/disabled integrations)
- [ ] Add “Entity hygiene” checks (unavailable entities count, etc.)
- [ ] Add export button: download `homeops-diagnostics.json`

## Phase 3 — Safe Change Engine v0 (NEXT)
**Goal:** Do *one* safe fix end-to-end.

Candidate safe fixes (pick 1):
- Fix #1: create a “Diagnostics” automation that notifies on `unavailable` entity spikes
- Fix #2: create a backup schedule (if HA supports /backup endpoints) or a reminder
- Fix #3: create a “Goodnight” scene using selected entities

System requirements:
- Always show “plan → preview → apply → verify”
- Always show “undo” if possible (where applicable)

## Phase 4 — Monetization experiment (LATER)
- Offer paid “HomeOps Cloud” for:
  - cross-home sync
  - remote agent help
  - premium templates
  - issue detection notifications

---

## Decisions log
- Wedge: HA add-on (not a standalone app yet)
- Pricing: TBD
