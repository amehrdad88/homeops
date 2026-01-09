# HomeOps Doctor (Home Assistant Add-on)

HomeOps Doctor is a local-first reliability dashboard for Home Assistant. It surfaces the *one* most important operational issue, explains impact, and gives clear “start here” steps.

This package is structured as a Home Assistant add-on repository:
- `repository.yaml` at repo root
- `homeops/` add-on folder (contains `config.yaml`, `Dockerfile`, app code)

## Install (Home Assistant OS)
1. Add repo in Settings → Add-ons → Add-on store → ⋮ → Repositories
2. Install **HomeOps**
3. Start, then open the UI from the sidebar

## Notes
- Read-only by design (no autofix, no AI, no config writes).
