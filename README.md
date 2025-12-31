# HomeOps (WIP)

HomeOps is an "Autopilot" layer for Home Assistant.

## v0 goal
A **read-only** Doctor UI that runs as a Home Assistant add-on using **Ingress**.

## Install (dev)
1. In Home Assistant: Settings → Add-ons → Add-on Store → (⋮) Repositories → add your GitHub repo URL.
2. Find "HomeOps" in the store, Install, Start.
3. Open the sidebar item "HomeOps".

## Notes
- This add-on uses the Home Assistant Core API proxy (`http://supervisor/core/api/`) and the `SUPERVISOR_TOKEN`.
