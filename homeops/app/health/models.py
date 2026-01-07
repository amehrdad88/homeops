from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

Severity = str  # "healthy" | "warning" | "critical" | "unknown"

@dataclass
class UpdateItem:
    entity_id: str
    installed: Optional[str] = None
    latest: Optional[str] = None

@dataclass
class UnavailableSummary:
    total_count: int = 0
    critical_count: int = 0
    by_domain: Dict[str, int] = field(default_factory=dict)
    sample_entities: List[str] = field(default_factory=list)

@dataclass
class UpdatesSummary:
    count: int = 0
    items: List[UpdateItem] = field(default_factory=list)

@dataclass
class Issue:
    id: str
    title: str
    severity: Severity
    summary: str
    start_here: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DoctorReport:
    ha_version: str = "unknown"
    entity_count: int = 0
    severity: Severity = "unknown"
    unavailable: UnavailableSummary = field(default_factory=UnavailableSummary)
    updates: UpdatesSummary = field(default_factory=UpdatesSummary)
    issues: List[Issue] = field(default_factory=list)
    generated_at_iso: str = ""
