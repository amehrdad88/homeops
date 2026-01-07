from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from .models import DoctorReport, UnavailableSummary, UpdatesSummary, UpdateItem, Issue
from .rules import IMPORTANT_DOMAINS, CRITICAL_UNAVAILABLE_THRESHOLD

def _classify_unavailable(states: List[Dict[str, Any]]):
    unavailable = []
    by_domain = defaultdict(list)
    critical = []

    for s in states:
        entity_id = s.get("entity_id", "")
        state = s.get("state")
        if state not in ("unavailable", "unknown"):
            continue

        unavailable.append(entity_id)
        domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
        by_domain[domain].append(entity_id)

        if domain in IMPORTANT_DOMAINS:
            critical.append(entity_id)

    by_domain_counts = {
        d: len(v) for d, v in sorted(by_domain.items(), key=lambda x: len(x[1]), reverse=True)
    }

    return unavailable, critical, by_domain_counts

def _find_pending_updates(states: List[Dict[str, Any]]):
    updates = []
    for s in states:
        entity_id = s.get("entity_id", "")
        if not entity_id.startswith("update."):
            continue
        state = s.get("state")
        attrs = s.get("attributes", {}) or {}
        latest = attrs.get("latest_version")
        installed = attrs.get("installed_version")

        if state == "on" or (latest and installed and latest != installed):
            updates.append(UpdateItem(entity_id=entity_id, installed=installed, latest=latest))
    return updates

def build_report(ha_version: str, states: List[Dict[str, Any]]) -> DoctorReport:
    report = DoctorReport()
    report.ha_version = ha_version or "unknown"
    report.entity_count = len(states)
    report.generated_at_iso = datetime.now(timezone.utc).isoformat()

    unavailable, critical_unavailable, by_domain = _classify_unavailable(states)
    updates = _find_pending_updates(states)

    # Severity
    if len(critical_unavailable) >= CRITICAL_UNAVAILABLE_THRESHOLD:
        report.severity = "critical"
    elif len(critical_unavailable) > 0 or len(updates) > 0:
        report.severity = "warning"
    else:
        report.severity = "healthy"

    report.unavailable = UnavailableSummary(
        total_count=len(unavailable),
        critical_count=len(critical_unavailable),
        by_domain=by_domain,
        sample_entities=unavailable[:50],
    )
    report.updates = UpdatesSummary(
        count=len(updates),
        items=updates,
    )

    # Issues (deterministic, read-only)
    if report.unavailable.critical_count > 0:
        report.issues.append(Issue(
            id="critical_unavailable",
            title=f"{report.unavailable.critical_count} critical devices unavailable",
            severity="critical" if report.severity == "critical" else "warning",
            summary="Core device domains (lights, climate, locks, media) are unavailable. This usually indicates an integration outage, coordinator issue, or network/device power problem.",
            start_here=[
                "Check whether the affected integration(s) show errors in Settings → Devices & services.",
                "If the affected devices are Zigbee/Z-Wave, verify the coordinator is online and not rebooting.",
                "If this started after an update/restart, review what changed recently before rebooting repeatedly.",
            ],
            evidence={
                "critical_count": report.unavailable.critical_count,
                "by_domain": list(report.unavailable.by_domain.items())[:10],
            }
        ))

    if report.updates.count > 0:
        report.issues.append(Issue(
            id="updates_pending",
            title=f"{report.updates.count} updates pending",
            severity="warning",
            summary="Updates can introduce breaking changes. Apply cautiously and keep backups.",
            start_here=[
                "Review release notes for Home Assistant core and impacted integrations.",
                "Create a backup before upgrading.",
                "Update one component at a time and verify key devices.",
            ],
            evidence={
                "updates": [u.__dict__ for u in report.updates.items[:10]],
            }
        ))

    if report.severity == "healthy":
        report.issues.append(Issue(
            id="healthy",
            title="No issues detected",
            severity="healthy",
            summary="HomeOps did not find availability or update issues.",
            start_here=["If something feels off, check recent logs and confirm devices are reachable."],
            evidence={}
        ))

    return report
