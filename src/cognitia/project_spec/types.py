"""Cognitia Project Directional Programming Types.

Implements the minimum generic project-specification kernel:
DirectionalRule, DirectionalSpec, ArchitectureCandidate, ScaffoldSpec,
Projection, EvidenceRequest, Conflict, Traceability.

All structures enforce deep immutability and deterministic provenance.
Domain-neutral: no adapter imports, no application-specific vocabulary.
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
from cognitia.provenance.record import ProvenanceRecord, SourceType


class DirectionalRuleStatus(str, enum.Enum):
    """Lifecycle status for a directional rule."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    VALIDATED = "validated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    UNRESOLVED = "unresolved"


class ConflictResolutionPolicy(str, enum.Enum):
    """Default policy when directional rules conflict."""

    ESCALATE_TO_GOVERNANCE = "escalate_to_governance"
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MERGE = "merge"


class ProjectionType(str, enum.Enum):
    """Supported projection relationships."""

    DIRECTION_TO_ARCHITECTURE = "direction_to_architecture"
    ARCHITECTURE_TO_SCAFFOLD = "architecture_to_scaffold"
    RULE_TO_ARCHITECTURE = "rule_to_architecture"
    ARCHITECTURE_TO_RULE = "architecture_to_rule"


class RelationshipType(str, enum.Enum):
    """Traceability relationship kinds."""

    DERIVES = "derives"
    IMPLEMENTS = "implements"
    REQUIRES = "requires"
    CONFLICTS = "conflicts"
    SUPERSEDES = "supersedes"
    TRACES_TO = "traces_to"


class DeliverySemantics(str, enum.Enum):
    """Delivery guarantee for an interaction boundary."""

    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"
    UNSPECIFIED = "unspecified"


# ------------------------------------------------------------------
# InteractionContract
# ------------------------------------------------------------------


@dataclass(frozen=True)
class InteractionContract(CognitiveObject):
    """Immutable interaction contract for a boundary.

    Expresses generic interaction requirements without prescribing
    transport technology or implementation procedure.
    """

    contract_id: str = ""
    boundary: str = ""
    canonical_representation: str = ""
    translation_required: bool = False
    delivery_semantics: str = DeliverySemantics.UNSPECIFIED.value
    idempotency_required: bool = False
    observables: tuple[str, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        contract_id: str = "",
        boundary: str = "",
        canonical_representation: str = "",
        translation_required: bool = False,
        delivery_semantics: str = DeliverySemantics.UNSPECIFIED.value,
        idempotency_required: bool = False,
        observables: Sequence[str] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "contract_id", str(contract_id))
        object.__setattr__(self, "boundary", str(boundary))
        object.__setattr__(self, "canonical_representation", str(canonical_representation))
        object.__setattr__(self, "translation_required", bool(translation_required))
        object.__setattr__(self, "delivery_semantics", str(delivery_semantics))
        object.__setattr__(self, "idempotency_required", bool(idempotency_required))
        object.__setattr__(self, "observables", tuple(observables))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="interaction_contract_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# DirectionalRule
# ------------------------------------------------------------------


@dataclass(frozen=True)
class DirectionalRule(CognitiveObject):
    """Immutable project directional rule.

    A rule declares desired project state, boundaries, and evidence
    requirements without prescribing implementation procedure.
    """

    rule_id: str = ""
    version: str = "1.0.0"
    status: DirectionalRuleStatus = DirectionalRuleStatus.DRAFT

    current_state: str = ""
    desired_state: str = ""
    objectives: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    allowed_authorities: tuple[str, ...] = ()
    prohibited_authorities: tuple[str, ...] = ()
    authority_boundaries: tuple[str, ...] = ()

    observables: tuple[str, ...] = ()
    acceptance_conditions: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    provenance_requirements: tuple[str, ...] = ()

    implementation_scope: str = ""
    governance_notes: str = ""
    conflict_policy: str = ConflictResolutionPolicy.ESCALATE_TO_GOVERNANCE.value

    scaffold_constraints: tuple[str, ...] = ()
    technology_freedoms: tuple[str, ...] = ()
    projection_requirements: tuple[str, ...] = ()
    interaction_contracts: tuple[InteractionContract, ...] = ()

    supersedes: str = ""
    superseded_by: str = ""

    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        rule_id: str = "",
        version: str = "1.0.0",
        status: DirectionalRuleStatus | str = DirectionalRuleStatus.DRAFT,
        current_state: str = "",
        desired_state: str = "",
        objectives: Sequence[str] = (),
        constraints: Sequence[str] = (),
        allowed_authorities: Sequence[str] = (),
        prohibited_authorities: Sequence[str] = (),
        authority_boundaries: Sequence[str] = (),
        observables: Sequence[str] = (),
        acceptance_conditions: Sequence[str] = (),
        evidence_requirements: Sequence[str] = (),
        provenance_requirements: Sequence[str] = (),
        implementation_scope: str = "",
        governance_notes: str = "",
        conflict_policy: str = ConflictResolutionPolicy.ESCALATE_TO_GOVERNANCE.value,
        scaffold_constraints: Sequence[str] = (),
        technology_freedoms: Sequence[str] = (),
        projection_requirements: Sequence[str] = (),
        interaction_contracts: Sequence[InteractionContract] = (),
        supersedes: str = "",
        superseded_by: str = "",
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "rule_id", str(rule_id))
        object.__setattr__(self, "version", str(version))
        if isinstance(status, str):
            status = DirectionalRuleStatus(status)
        object.__setattr__(self, "status", status)

        object.__setattr__(self, "current_state", str(current_state))
        object.__setattr__(self, "desired_state", str(desired_state))
        object.__setattr__(self, "objectives", tuple(objectives))
        object.__setattr__(self, "constraints", tuple(constraints))

        object.__setattr__(self, "allowed_authorities", tuple(allowed_authorities))
        object.__setattr__(self, "prohibited_authorities", tuple(prohibited_authorities))
        object.__setattr__(self, "authority_boundaries", tuple(authority_boundaries))

        object.__setattr__(self, "observables", tuple(observables))
        object.__setattr__(self, "acceptance_conditions", tuple(acceptance_conditions))
        object.__setattr__(self, "evidence_requirements", tuple(evidence_requirements))
        object.__setattr__(self, "provenance_requirements", tuple(provenance_requirements))

        object.__setattr__(self, "implementation_scope", str(implementation_scope))
        object.__setattr__(self, "governance_notes", str(governance_notes))
        object.__setattr__(self, "conflict_policy", str(conflict_policy))

        object.__setattr__(self, "scaffold_constraints", tuple(scaffold_constraints))
        object.__setattr__(self, "technology_freedoms", tuple(technology_freedoms))
        object.__setattr__(self, "projection_requirements", tuple(projection_requirements))
        object.__setattr__(self, "interaction_contracts", tuple(interaction_contracts))

        object.__setattr__(self, "supersedes", str(supersedes))
        object.__setattr__(self, "superseded_by", str(superseded_by))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="directional_rule_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# DirectionalSpec
# ------------------------------------------------------------------


@dataclass(frozen=True)
class DirectionalSpec(CognitiveObject):
    """Immutable project directional specification.

    A specification groups related directional rules and declares
    the overall project intent without prescribing implementation.
    """

    rules: tuple[DirectionalRule, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        rules: Sequence[DirectionalRule] = (),
        metadata: Mapping[str, Any] | None = None,
        provenance: ProvenanceRecord | None = None,
        id: str | None = None,
    ) -> None:
        object.__setattr__(self, "id", str(id) if id else generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "rules", tuple(rules))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="directional_spec_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# ArchitectureCandidate
# ------------------------------------------------------------------


@dataclass(frozen=True)
class ArchitectureCandidate(CognitiveObject):
    """Immutable candidate architecture derived from directional rules.

    Invariants:
    1. A candidate represents a possible architecture, not an accepted one.
    2. Every architectural element should trace back to one or more rules.
    3. Candidates do not prescribe exact implementations.
    """

    candidate_id: str = ""
    boundaries: tuple[str, ...] = ()
    authorities: tuple[str, ...] = ()
    responsibilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    prohibited_dependencies: tuple[str, ...] = ()
    observables: tuple[str, ...] = ()
    validation_requirements: tuple[str, ...] = ()
    interaction_contracts: tuple[str, ...] = ()
    traceability: tuple[str, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE
        )
    )

    def __init__(
        self,
        candidate_id: str = "",
        boundaries: Sequence[str] = (),
        authorities: Sequence[str] = (),
        responsibilities: Sequence[str] = (),
        dependencies: Sequence[str] = (),
        invariants: Sequence[str] = (),
        required_capabilities: Sequence[str] = (),
        prohibited_dependencies: Sequence[str] = (),
        observables: Sequence[str] = (),
        validation_requirements: Sequence[str] = (),
        interaction_contracts: Sequence[str] = (),
        traceability: Sequence[str] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "candidate_id", str(candidate_id))
        object.__setattr__(self, "boundaries", tuple(boundaries))
        object.__setattr__(self, "authorities", tuple(authorities))
        object.__setattr__(self, "responsibilities", tuple(responsibilities))
        object.__setattr__(self, "dependencies", tuple(dependencies))
        object.__setattr__(self, "invariants", tuple(invariants))
        object.__setattr__(self, "required_capabilities", tuple(required_capabilities))
        object.__setattr__(self, "prohibited_dependencies", tuple(prohibited_dependencies))
        object.__setattr__(self, "observables", tuple(observables))
        object.__setattr__(self, "validation_requirements", tuple(validation_requirements))
        object.__setattr__(self, "interaction_contracts", tuple(interaction_contracts))
        object.__setattr__(self, "traceability", tuple(traceability))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="architecture_candidate_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# ScaffoldSpec
# ------------------------------------------------------------------


@dataclass(frozen=True)
class ScaffoldSpec(CognitiveObject):
    """Immutable scaffold specification derived from an architecture candidate.

    A scaffold spec declares required structural surfaces without
    prescribing exact implementation code, classes, or libraries.
    """

    spec_id: str = ""
    required_boundaries: tuple[str, ...] = ()
    required_surfaces: tuple[str, ...] = ()
    required_interfaces: tuple[str, ...] = ()
    required_contract_surfaces: tuple[str, ...] = ()
    required_test_surfaces: tuple[str, ...] = ()
    prohibited_structural_patterns: tuple[str, ...] = ()
    implementation_freedoms: tuple[str, ...] = ()
    interaction_contracts: tuple[str, ...] = ()
    traceability: tuple[str, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE
        )
    )

    def __init__(
        self,
        spec_id: str = "",
        required_boundaries: Sequence[str] = (),
        required_surfaces: Sequence[str] = (),
        required_interfaces: Sequence[str] = (),
        required_contract_surfaces: Sequence[str] = (),
        required_test_surfaces: Sequence[str] = (),
        prohibited_structural_patterns: Sequence[str] = (),
        implementation_freedoms: Sequence[str] = (),
        interaction_contracts: Sequence[str] = (),
        traceability: Sequence[str] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "spec_id", str(spec_id))
        object.__setattr__(self, "required_boundaries", tuple(required_boundaries))
        object.__setattr__(self, "required_surfaces", tuple(required_surfaces))
        object.__setattr__(self, "required_interfaces", tuple(required_interfaces))
        object.__setattr__(self, "required_contract_surfaces", tuple(required_contract_surfaces))
        object.__setattr__(self, "required_test_surfaces", tuple(required_test_surfaces))
        object.__setattr__(self, "prohibited_structural_patterns", tuple(prohibited_structural_patterns))
        object.__setattr__(self, "implementation_freedoms", tuple(implementation_freedoms))
        object.__setattr__(self, "interaction_contracts", tuple(interaction_contracts))
        object.__setattr__(self, "traceability", tuple(traceability))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="scaffold_spec_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# Projection
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Projection(CognitiveObject):
    """Immutable record of a derivation from one artifact to another."""

    source_id: str = ""
    target_id: str = ""
    projection_type: str = ""
    source_references: tuple[str, ...] = ()
    result_references: tuple[str, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE
        )
    )

    def __init__(
        self,
        source_id: str = "",
        target_id: str = "",
        projection_type: str = "",
        source_references: Sequence[str] = (),
        result_references: Sequence[str] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "source_id", str(source_id))
        object.__setattr__(self, "target_id", str(target_id))
        object.__setattr__(self, "projection_type", str(projection_type))
        object.__setattr__(self, "source_references", tuple(source_references))
        object.__setattr__(self, "result_references", tuple(result_references))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="projection_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# EvidenceRequest
# ------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceRequest(CognitiveObject):
    """Request for evidence concerning a rule or projection."""

    request_id: str = ""
    rule_id: str = ""
    projection_id: str = ""
    evidence_type: str = ""
    acceptance_condition: str = ""
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        request_id: str = "",
        rule_id: str = "",
        projection_id: str = "",
        evidence_type: str = "",
        acceptance_condition: str = "",
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "request_id", str(request_id))
        object.__setattr__(self, "rule_id", str(rule_id))
        object.__setattr__(self, "projection_id", str(projection_id))
        object.__setattr__(self, "evidence_type", str(evidence_type))
        object.__setattr__(self, "acceptance_condition", str(acceptance_condition))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="evidence_request_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# Conflict
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Conflict(CognitiveObject):
    """Immutable record of conflicting directional rules or projections."""

    conflict_id: str = ""
    rules_in_conflict: tuple[str, ...] = ()
    description: str = ""
    affected_projection: str = ""
    severity: str = "medium"
    resolution_status: str = "open"
    governance_required: bool = True
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        conflict_id: str = "",
        rules_in_conflict: Sequence[str] = (),
        description: str = "",
        affected_projection: str = "",
        severity: str = "medium",
        resolution_status: str = "open",
        governance_required: bool = True,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "conflict_id", str(conflict_id))
        object.__setattr__(self, "rules_in_conflict", tuple(rules_in_conflict))
        object.__setattr__(self, "description", str(description))
        object.__setattr__(self, "affected_projection", str(affected_projection))
        object.__setattr__(self, "severity", str(severity))
        object.__setattr__(self, "resolution_status", str(resolution_status))
        object.__setattr__(self, "governance_required", bool(governance_required))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="conflict_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


# ------------------------------------------------------------------
# Traceability
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Traceability(CognitiveObject):
    """Immutable traceability link between two artifacts."""

    source_id: str = ""
    target_id: str = ""
    relationship: str = ""
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        source_id: str = "",
        target_id: str = "",
        relationship: str = "",
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "source_id", str(source_id))
        object.__setattr__(self, "target_id", str(target_id))
        object.__setattr__(self, "relationship", str(relationship))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="traceability_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class ProjectionResult(CognitiveObject):
    """Immutable aggregate result of a complete projection chain.

    Invariants:
    1. ProjectionResult is a candidate artifact, not an accepted structure.
    2. ProjectionResult does not constitute governance approval.
    3. ProjectionResult does not generate implementation code.
    """

    specification_id: str = ""
    architecture_candidate: ArchitectureCandidate | None = None
    scaffold_spec: ScaffoldSpec | None = None
    projections: tuple[Projection, ...] = ()
    traceability: tuple[Traceability, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE
        )
    )

    def __init__(
        self,
        specification_id: str = "",
        architecture_candidate: ArchitectureCandidate | None = None,
        scaffold_spec: ScaffoldSpec | None = None,
        projections: Sequence[Projection] = (),
        traceability: Sequence[Traceability] = (),
        conflicts: Sequence[Conflict] = (),
        metadata: Mapping[str, Any] | None = None,
        provenance: ProvenanceRecord | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "specification_id", str(specification_id))
        object.__setattr__(self, "architecture_candidate", architecture_candidate)
        object.__setattr__(self, "scaffold_spec", scaffold_spec)
        object.__setattr__(self, "projections", tuple(projections))
        object.__setattr__(self, "traceability", tuple(traceability))
        object.__setattr__(self, "conflicts", tuple(conflicts))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="projection_result_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))
