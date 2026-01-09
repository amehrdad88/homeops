from collections import defaultdict
from typing import Any, Dict, Iterable, List

IMPORTANT_DOMAINS = {"light","switch","lock","climate","cover","fan","media_player"}

def analyze_health(states: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    unavailable: List[str] = []
    critical_unavailable: List[str] = []
    by_domain = defaultdict(list)
    updates: List[Dict[str, Any]] = []

    for s in states:
        entity_id = s.get("entity_id","")
        st = (s.get("state") or "")
        attrs = s.get("attributes", {}) or {}
        domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

        if st in ("unavailable","unknown"):
            unavailable.append(entity_id)
            by_domain[domain].append(entity_id)
            if domain in IMPORTANT_DOMAINS:
                critical_unavailable.append(entity_id)

        if domain == "update":
            latest = attrs.get("latest_version")
            installed = attrs.get("installed_version")
            if st == "on" or (latest and installed and latest != installed):
                updates.append({"entity_id": entity_id, "installed": installed, "latest": latest})

    if len(critical_unavailable) >= 5:
        severity = "critical"
    elif critical_unavailable or updates:
        severity = "warning"
    else:
        severity = "healthy"

    sorted_domain_counts = {
        d: len(v) for d, v in sorted(by_domain.items(), key=lambda kv: len(kv[1]), reverse=True)
    }

    return {
        "severity": severity,
        "unavailable": {
            "total_count": len(unavailable),
            "critical_count": len(critical_unavailable),
            "by_domain": sorted_domain_counts,
        },
        "updates": {"count": len(updates), "items": updates},
    }

def build_report(health: Dict[str, Any]) -> Dict[str, Any]:
    sev = health.get("severity","unknown")
    unav = health.get("unavailable", {})
    upd = health.get("updates", {})

    crit = int(unav.get("critical_count", 0) or 0)
    updates_n = int(upd.get("count", 0) or 0)

    if sev == "healthy":
        return {
            "headline": "Everything looks healthy",
            "severity": "healthy",
            "description": "HomeOps didn’t detect availability or update issues affecting core devices.",
            "start_here": [],
            "details": "",
        }

    if crit > 0:
        headline = f"{crit} core devices are unavailable"
        description = "This usually points to one failing integration, coordinator instability, or a local network/device power issue."
        start_here = [
            "Open Settings → Devices & services and look for an integration with errors.",
            "If Zigbee/Z‑Wave is involved, confirm the coordinator is online and stable.",
            "Avoid repeated restarts; identify what changed (updates/restarts) first.",
        ]
        details = ""
        return {"headline": headline, "severity": "critical" if crit >= 5 else "warning", "description": description, "start_here": start_here, "details": details}

    if updates_n > 0:
        headline = f"{updates_n} updates are pending"
        description = "Updates can introduce breaking changes. Apply cautiously."
        start_here = [
            "Review release notes for Home Assistant core and impacted integrations.",
            "Create a backup before upgrading.",
            "Update one component at a time and verify key devices.",
        ]
        return {"headline": headline, "severity": "warning", "description": description, "start_here": start_here, "details": ""}

    return {
        "headline": "Issues detected",
        "severity": "warning",
        "description": "HomeOps detected issues but couldn’t classify them as core-device outages.",
        "start_here": ["Check Devices & services for errors and review recent changes."],
        "details": "",
    }
