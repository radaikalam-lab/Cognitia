"""Cognitia Cognitive Rule and Human-Governed Intelligence Types.

Defines schemas for domain-neutral cognitive rules, rule lifecycle states,
and human/operator provenance for cognitive intelligence artifacts.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class RuleStatus(str, enum.Enum):
    """Lifecycle status of a Cognitive Rule."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    DRAFT = "draft"


@dataclass(frozen=True)
class CognitiveRule(CognitiveObject):
    """Immutable, versioned cognitive rule artifact.
    
    Represents human-authored or validated cognitive intelligence.
    Once published, a rule version is immutable. Changes result in Version N+1.
    """

    rule_id: str = field(default_factory=generate_entity_id)
    version: str = "1.0.0"
    name: str = "Unnamed Rule"
    description: str = ""
    scope: str = "general"
    predicate: dict[str, Any] = field(default_factory=dict)
    recommendation: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    confidence: float = 1.0
    author_id: str = "human_operator"
    status: RuleStatus = RuleStatus.ACTIVE
    parent_rule_version_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id="human_operator",
            is_deterministic=True,
        )
    )
