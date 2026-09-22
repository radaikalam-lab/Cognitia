"""Cognitia Directional Programming Types.

Defines provider-neutral directional specifications, objectives, constraints,
success criteria, proposals, residuals, and lifecycle states.
All structures enforce deep immutability and snapshot safety.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.providers.types import ProposalLifecycleStatus


class DirectionalResidualType(str, enum.Enum):
    """Explicit residual categories for directional proposal evaluation."""

    TARGET_UNDEFINED = "target_undefined"
    CONSTRAINT_VIOLATED = "constraint_violated"
    CONFLICTING_OBJECTIVES = "conflicting_objectives"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    KNOWLEDGE_GAP = "knowledge_gap"
    AMBIGUOUS_CRITERIA = "ambiguous_criteria"


@dataclass(frozen=True)
class DirectionalObjective(CognitiveObject):
    """Declarative desired outcome for a directional specification."""

    description: str = ""
    target_state: tuple[tuple[str, Any], ...] = ()
    priority: float = 1.0
    metrics: tuple[str, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        description: str = "",
        target_state: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        priority: float = 1.0,
        metrics: Sequence[str] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        if target_state is None:
            target_state_tuple: tuple[tuple[str, Any], ...] = ()
        elif isinstance(target_state, Mapping):
            target_state_tuple = tuple(target_state.items())
        else:
            target_state_tuple = tuple(target_state)

        object.__setattr__(self, "description", str(description))
        object.__setattr__(self, "target_state", target_state_tuple)
        object.__setattr__(self, "priority", float(priority))
        object.__setattr__(self, "metrics", tuple(metrics))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="directional_objective_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def target_state_dict(self) -> dict[str, Any]:
        return dict(self.target_state)


@dataclass(frozen=True)
class DirectionalConstraint(CognitiveObject):
    """Boundary or limit governing how objectives may be achieved."""

    description: str = ""
    constraint_type: str = "soft"
    bound: tuple[tuple[str, Any], ...] = ()
    is_hard: bool = False
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        description: str = "",
        constraint_type: str = "soft",
        bound: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        is_hard: bool = False,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        if bound is None:
            bound_tuple: tuple[tuple[str, Any], ...] = ()
        elif isinstance(bound, Mapping):
            bound_tuple = tuple(bound.items())
        else:
            bound_tuple = tuple(bound)

        object.__setattr__(self, "description", str(description))
        object.__setattr__(self, "constraint_type", str(constraint_type))
        object.__setattr__(self, "bound", bound_tuple)
        object.__setattr__(self, "is_hard", bool(is_hard))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="directional_constraint_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def bound_dict(self) -> dict[str, Any]:
        return dict(self.bound)


@dataclass(frozen=True)
class SuccessCriterion(CognitiveObject):
    """Quantifiable measure for evaluating whether a proposal satisfies an objective."""

    description: str = ""
    metric_name: str = ""
    threshold: float = 0.0
    direction: str = ">="
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        description: str = "",
        metric_name: str = "",
        threshold: float = 0.0,
        direction: str = ">=",
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "description", str(description))
        object.__setattr__(self, "metric_name", str(metric_name))
        object.__setattr__(self, "threshold", float(threshold))
        object.__setattr__(self, "direction", str(direction))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="directional_criterion_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DirectionalSpecification(CognitiveObject):
    """Immutable, versioned, provenance-tracked declaration of desired cognitive outcomes.

    INVARIANTS:
    1. A specification declares what to achieve, not how to achieve it.
    2. Specifications contain no execution logic, actuator bindings, or hardware directives.
    3. Specifications are immutable once created; revision requires creating a new versioned specification.
    """

    objectives: tuple[DirectionalObjective, ...] = ()
    constraints: tuple[DirectionalConstraint, ...] = ()
    success_criteria: tuple[SuccessCriterion, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        objectives: Sequence[DirectionalObjective] = (),
        constraints: Sequence[DirectionalConstraint] = (),
        success_criteria: Sequence[SuccessCriterion] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "objectives", tuple(objectives))
        object.__setattr__(self, "constraints", tuple(constraints))
        object.__setattr__(self, "success_criteria", tuple(success_criteria))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="directional_specification_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DirectionalResidual(CognitiveObject):
    """Explicit explanation of why a proposal cannot fully satisfy a specification."""

    factor_name: str = ""
    description: str = ""
    residual_type: DirectionalResidualType = DirectionalResidualType.KNOWLEDGE_GAP
    target_variable: str | None = None
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        factor_name: str = "",
        description: str = "",
        residual_type: DirectionalResidualType | str = DirectionalResidualType.KNOWLEDGE_GAP,
        target_variable: str | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "factor_name", str(factor_name))
        object.__setattr__(self, "description", str(description))
        if isinstance(residual_type, str):
            residual_type = DirectionalResidualType(residual_type)
        object.__setattr__(self, "residual_type", residual_type)
        object.__setattr__(self, "target_variable", target_variable)

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="directional_residual_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DirectionalProposal(CognitiveObject):
    """Immutable candidate solution to a directional specification.

    INVARIANTS:
    1. New proposals start with epistemic_status = UNRESOLVED and proposal_status = PROPOSED.
    2. Proposals are advisory; they never represent physical truth or execution authority.
    3. Residuals MUST be reported for any unachievable or violated aspects.
    """

    specification_id: str = ""
    provider_id: str = ""
    provider_version: str = "1.0.0"
    proposed_actions: tuple[tuple[str, Any], ...] = ()
    residuals: tuple[DirectionalResidual, ...] = ()
    confidence: float = 1.0
    proposal_status: ProposalLifecycleStatus = ProposalLifecycleStatus.PROPOSED
    epistemic_status: EpistemicStatus = EpistemicStatus.UNRESOLVED
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.REASONING_ENGINE)
    )

    def __init__(
        self,
        specification_id: str = "",
        provider_id: str = "",
        provider_version: str = "1.0.0",
        proposed_actions: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        residuals: Sequence[DirectionalResidual] = (),
        confidence: float = 1.0,
        proposal_status: ProposalLifecycleStatus = ProposalLifecycleStatus.PROPOSED,
        epistemic_status: EpistemicStatus = EpistemicStatus.UNRESOLVED,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "specification_id", str(specification_id))
        object.__setattr__(self, "provider_id", str(provider_id))
        object.__setattr__(self, "provider_version", str(provider_version))

        if proposed_actions is None:
            actions_tuple: tuple[tuple[str, Any], ...] = ()
        elif isinstance(proposed_actions, Mapping):
            actions_tuple = tuple(proposed_actions.items())
        else:
            actions_tuple = tuple(proposed_actions)

        object.__setattr__(self, "proposed_actions", actions_tuple)
        object.__setattr__(self, "residuals", tuple(residuals))
        object.__setattr__(self, "confidence", float(confidence))
        object.__setattr__(self, "proposal_status", proposal_status)
        object.__setattr__(self, "epistemic_status", epistemic_status)

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id=f"directional_provider:{provider_id}:{provider_version}",
            parent_ids=[specification_id],
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def proposed_actions_dict(self) -> dict[str, Any]:
        return dict(self.proposed_actions)
