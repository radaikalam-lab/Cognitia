"""Frappe Read-Only Advisory Presentation.

Defines the non-authoritative advisory data structure returned by Cognitia to Frappe.
Advisories are informational only and possess zero execution authority over ERP documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import Decision


@dataclass(frozen=True)
class FrappeAdvisory:
    """Non-authoritative cognitive advisory presented to a Frappe user or interface.
    
    INVARIANT:
    FrappeAdvisory is strictly read-only. It provides cognitive context and suggestions
    without possessing execution authority or the ability to alter ERP transactions.
    """

    document_type: str
    document_name: str
    historical_context_summary: str
    similar_experiences_count: int = 0
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
        """Convert advisory to serializable dictionary for Frappe desk/UI rendering."""
        return {
            "document_type": self.document_type,
            "document_name": self.document_name,
            "historical_context_summary": self.historical_context_summary,
            "similar_experiences_count": self.similar_experiences_count,
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
