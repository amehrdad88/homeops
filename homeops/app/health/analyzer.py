"""Functions for analyzing Home Assistant state and producing reports.

This module contains two primary functions:
  * :func:`analyze_health` takes the raw list of entity states and returns a
    structured summary of counts and severity levels.
  * :func:`build_report` takes that summary and constructs an opinionated
    message that emphasises the most important issue and suggests clear
    next steps.  This is what the user sees in the UI.

The goal is to provide a single source of truth for health analysis so
that both the HTML view and any future integrations (e.g. API clients,
Discord bots) can rely on the same underlying logic.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

IMPORTANT_DOMAINS = {
    "light",
    "switch",
    "lock",
    "climate",
    "cover",
    "fan",
    "media_player",
}


def analyze_health(states: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute a deterministic health summary from a list of entity states.

    Parameters
    ----------
    states: Iterable of entity state dictionaries returned by `/api/states`.

    Returns
    -------
    A nested dictionary with keys:

    ``severity``
        One of ``"critical"``, ``"warning"``, or ``"healthy"``
        indicating the overall state of the system.

    ``unavailable``
        A dictionary containing counts of unavailable entities and
        groupings by domain.  Keys:

        ``total_count``
            Total number of entities whose state is ``"unavailable"`` or
            ``"unknown"``.

        ``critical_count``
            The number of unavailable entities whose domain is in
            ``IMPORTANT_DOMAINS``.

        ``by_domain``
            A mapping from domain name (string) to count of
            unavailable entities in that domain, sorted descending.

    ``updates``
        Information about pending updates.  Keys:

        ``count``
            The number of update entities reporting an available update.

        ``items``
            A list of dictionaries containing ``entity_id``, ``installed``,
            and ``latest`` for each update entity with an available update.
    """
    unavailable: List[str] = []
    critical_unavailable: List[str] = []
    by_domain: Dict[str, List[str]] = defaultdict(list)
    updates: List[Dict[str, Any]] = []

    for state in states:
        entity_id: str = state.get("entity_id", "")
        entity_state: str = state.get("state") or ""
        attrs: Dict[str, Any] = state.get("attributes", {})

        # Normalize domain name
        domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

        # Track unavailable entities
        if entity_state in ("unavailable", "unknown"):
            unavailable.append(entity_id)
            by_domain[domain].append(entity_id)
            if domain in IMPORTANT_DOMAINS:
                critical_unavailable.append(entity_id)

        # Track updates
        if domain == "update":
            latest = attrs.get("latest_version")
            installed = attrs.get("installed_version")
            # state == 'on' also indicates an update is available
            if entity_state == "on" or (latest and installed and latest != installed):
                updates.append(
                    {
                        "entity_id": entity_id,
                        "installed": installed,
                        "latest": latest,
                    }
                )

    # Determine severity
    if len(critical_unavailable) >= 5:
        severity = "critical"
    elif critical_unavailable or updates:
        severity = "warning"
    else:
        severity = "healthy"

    # Sort domain counts descending
    sorted_domain_counts: Dict[str, int] = {
        domain: len(entities)
        for domain, entities in sorted(by_domain.items(), key=lambda item: len(item[1]), reverse=True)
    }

    return {
        "severity": severity,
        "unavailable": {
            "total_count": len(unavailable),
            "critical_count": len(critical_unavailable),
            "by_domain": sorted_domain_counts,
        },
        "updates": {
            "count": len(updates),
            "items": updates,
        },
    }


def build_report(health: Dict[str, Any]) -> Dict[str, Any]:
    """Construct an opinionated report from the health summary.

    The report emphasises the most important issue, provides a short
    explanation, suggests concrete first steps, and includes a short
    description of why the issue likely occurred.  If the system is
    healthy, a reassuring message is returned instead.
    """
    unavailable = health.get("unavailable", {})
    updates = health.get("updates", {})
    severity = health.get("severity")

    if severity == "healthy":
        return {
            "headline": "No critical issues detected",
            "description": "All core devices appear to be operating normally.",
            "start_here": [],
            "details": "",
        }

    # Build headline and description
    crit_count = unavailable.get("critical_count", 0)
    headline = f"{crit_count} critical devices unavailable"

    description = (
        "Core device domains (lights, climate, locks, media) are unavailable. "
        "This usually indicates an integration outage, coordinator issue, or network/device power problem."
    )

    # Build a start-here list of concrete steps
    start_here: List[str] = [
        "Check whether the affected integration(s) show errors in Settings → Devices & services.",
        "If the affected devices are Zigbee/Z-Wave, verify the coordinator is online and not rebooting.",
        "If this started after an update or restart, review what changed recently before rebooting repeatedly.",
    ]

    # Build details: show the top three impacted domains and the count in parentheses
    by_domain = unavailable.get("by_domain", {})
    # Only include domains that are important or have significant impact
    impacted = [
        f"{domain} ({count})"
        for domain, count in by_domain.items()
        if domain in IMPORTANT_DOMAINS
    ]
    # If no important domains found, include the top domain anyway
    if not impacted and by_domain:
        top_domain, count = next(iter(by_domain.items()))
        impacted.append(f"{top_domain} ({count})")

    details = "Most affected domains: " + ", ".join(impacted) if impacted else ""

    return {
        "headline": headline,
        "description": description,
        "start_here": start_here,
        "details": details,
    }