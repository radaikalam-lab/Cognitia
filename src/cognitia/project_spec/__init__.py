"""Cognitia Project Directional Programming Module.

Provides a generic, domain-independent project specification kernel:
DirectionalRule, DirectionalSpec, ArchitectureCandidate, ScaffoldSpec,
Projection, EvidenceRequest, Conflict, Traceability.

This module is distinct from cognitia.directional (Cognitive Directional
Programming).  Project directional programming concerns non-procedural
project intent projected into architecture and scaffold specifications.
"""

from __future__ import annotations

from cognitia.project_spec.types import (
    ArchitectureCandidate,
    Conflict,
    ConflictResolutionPolicy,
    DeliverySemantics,
    DirectionalRule,
    DirectionalRuleStatus,
    DirectionalSpec,
    EvidenceRequest,
    InteractionContract,
    Projection,
    ProjectionResult,
    ProjectionType,
    RelationshipType,
    ScaffoldSpec,
    Traceability,
)
from cognitia.project_spec.service import (
    InMemoryProjectSpecService,
    ProjectSpecService,
)
from cognitia.project_spec.provider import (
    DeterministicProjectionProvider,
    ProjectionProvider,
)
from cognitia.project_spec.projection import (
    InMemoryProjectionService,
    ProjectionService,
)

__all__ = [
    "ArchitectureCandidate",
    "Conflict",
    "ConflictResolutionPolicy",
    "DeliverySemantics",
    "DirectionalRule",
    "DirectionalRuleStatus",
    "DirectionalSpec",
    "DeterministicProjectionProvider",
    "EvidenceRequest",
    "InMemoryProjectionService",
    "InMemoryProjectSpecService",
    "InteractionContract",
    "Projection",
    "ProjectionProvider",
    "ProjectionResult",
    "ProjectionService",
    "ProjectionType",
    "RelationshipType",
    "ScaffoldSpec",
    "Traceability",
]
