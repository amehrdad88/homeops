"""Dataclass definitions for health reports.

This module defines simple dataclasses representing the health state
and report structure.  While Python dictionaries are currently
sufficient, these classes can be used for static type checking or
future extensions.  They are kept simple to avoid runtime overhead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class HealthSummary:
    """Summary of the Home Assistant health state."""

    severity: str
    total_unavailable: int
    critical_unavailable: int
    by_domain: Dict[str, int]
    update_count: int


@dataclass
class HealthReport:
    """Opinionated human‑readable report based on a health summary."""

    headline: str
    description: str
    start_here: List[str] = field(default_factory=list)
    details: str = ""