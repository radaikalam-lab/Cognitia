"""Flash Joule Heating (FJH) Read-Only Advisory Presentation.

Defines the non-authoritative advisory data structure returned by Cognitia to FJH operators.
Advisories are informational only and possess zero execution authority over FJH hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import Decision


@dataclass(frozen=True)
class FJHAdvisory:
    """Non-authoritative cognitive advisory presented to an FJH operator or interface.

    INVARIANT:
    FJHAdvisory is strictly read-only. It provides cognitive context and suggestions
    without possessing execution authority or the ability to actuate FJH hardware.
    """

    experiment_id: str
    stage: str
    historical_context_summary: str
    similar_experiments_count: int = 0
    epistemic_status: str = "SUPPORTED"
    evidence_count: int = 0
    triggered_rule_id: str | None = None
    triggered_rule_version: str | None = None
    recommendation: str = ""
    confidence: float = 1.0
    decision: Decision | None = None
    is_authoritative: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert advisory to serializable dictionary for FJH UI rendering."""
        return {
            "experiment_id": self.experiment_id,
            "stage": self.stage,
            "historical_context_summary": self.historical_context_summary,
            "similar_experiments_count": self.similar_experiments_count,
            "epistemic_status": self.epistemic_status,
            "evidence_count": self.evidence_count,
            "triggered_rule_id": self.triggered_rule_id,
            "triggered_rule_version": self.triggered_rule_version,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "is_authoritative": self.is_authoritative,
            "decision_id": self.decision.id if self.decision else None,
            "metadata": self.metadata,
        }

    def serialize(self) -> str:
        """Serialize advisory to deterministic JSON string."""
        from cognitia.abi.types import DeterministicSerializer
        return DeterministicSerializer.serialize(self)
