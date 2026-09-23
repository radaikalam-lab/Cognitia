"""Cognitia Project Directional Programming Provider SPI.

Defines the provider-neutral interface for project directional projections
and a deterministic baseline reference implementation.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from cognitia.abi.types import generate_entity_id
from cognitia.project_spec.types import (
    ArchitectureCandidate,
    Conflict,
    DirectionalRule,
    DirectionalSpec,
    DirectionalRuleStatus,
    EvidenceRequest,
    Projection,
    ProjectionType,
    ScaffoldSpec,
    Traceability,
)


@runtime_checkable
class ProjectionProvider(Protocol):
    """Protocol for project directional projection providers."""

    provider_id: str
    provider_version: str

    def project_rule_to_architecture(
        self,
        rule: DirectionalRule,
    ) -> ArchitectureCandidate: ...

    def project_architecture_to_scaffold(
        self,
        candidate: ArchitectureCandidate,
    ) -> ScaffoldSpec: ...

    def detect_conflicts(
        self,
        rules: list[DirectionalRule],
    ) -> list[Conflict]: ...

    def build_traceability(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> Traceability: ...


class DeterministicProjectionProvider:
    """Deterministic baseline project directional projection provider.

    Derives candidate architecture and scaffold specifications from
    directional rules without inventing implementation details.

    This provider contains no AI/ML/network/filesystem dependencies.
    """

    def __init__(
        self,
        provider_id: str = "deterministic_projection_provider",
        provider_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version

    def project_rule_to_architecture(
        self,
        rule: DirectionalRule,
    ) -> ArchitectureCandidate:
        """Derive an architecture candidate from a single directional rule.

        Derivation rules:
        - allowed_authorities -> authorities
        - prohibited_authorities + authority_boundaries -> boundaries
        - objectives + constraints -> responsibilities
        - observables + acceptance_conditions -> observables + validation_requirements
        - technology_freedoms -> preserved as implementation freedoms
        - rule_id -> traceability
        """
        boundaries: list[str] = []
        boundaries.extend(rule.authority_boundaries)
        boundaries.extend(
            f"prohibited:{authority}" for authority in rule.prohibited_authorities
        )

        responsibilities: list[str] = []
        responsibilities.extend(rule.objectives)
        responsibilities.extend(rule.constraints)

        validation_requirements: list[str] = []
        validation_requirements.extend(rule.acceptance_conditions)
        validation_requirements.extend(rule.evidence_requirements)

        traceability_refs: list[str] = []
        if rule.rule_id:
            traceability_refs.append(rule.rule_id)
        if rule.supersedes:
            traceability_refs.append(f"supersedes:{rule.supersedes}")

        candidate = ArchitectureCandidate(
            candidate_id=f"arch-{rule.rule_id}" if rule.rule_id else "",
            boundaries=boundaries,
            authorities=rule.allowed_authorities,
            responsibilities=responsibilities,
            invariants=rule.constraints,
            required_capabilities=rule.projection_requirements,
            prohibited_dependencies=[
                f"prohibited_authority:{authority}"
                for authority in rule.prohibited_authorities
            ],
            observables=rule.observables,
            validation_requirements=validation_requirements,
            traceability=traceability_refs,
            interaction_contracts=tuple(
                contract.contract_id or contract.id for contract in rule.interaction_contracts
            ),
        )
        return candidate

    def project_architecture_to_scaffold(
        self,
        candidate: ArchitectureCandidate,
    ) -> ScaffoldSpec:
        """Derive a scaffold specification from an architecture candidate.

        Derivation rules:
        - boundaries -> required_boundaries
        - required_capabilities -> required_interfaces
        - validation_requirements -> required_test_surfaces
        - prohibited_dependencies -> prohibited_structural_patterns
        - traceability -> preserved
        """
        required_interfaces: list[str] = []
        required_interfaces.extend(candidate.required_capabilities)

        required_test_surfaces: list[str] = []
        required_test_surfaces.extend(candidate.validation_requirements)

        prohibited_structural_patterns: list[str] = []
        prohibited_structural_patterns.extend(candidate.prohibited_dependencies)

        implementation_freedoms: list[str] = []
        if candidate.authorities:
            implementation_freedoms.append("authority_boundaries_preserved")
        if candidate.invariants:
            implementation_freedoms.append("invariants_enforced")

        scaffold = ScaffoldSpec(
            spec_id=f"scf-{candidate.candidate_id}" if candidate.candidate_id else "",
            required_boundaries=candidate.boundaries,
            required_surfaces=candidate.authorities,
            required_interfaces=required_interfaces,
            required_test_surfaces=required_test_surfaces,
            prohibited_structural_patterns=prohibited_structural_patterns,
            implementation_freedoms=implementation_freedoms,
            traceability=list(candidate.traceability),
        )
        return scaffold

    def detect_conflicts(
        self,
        rules: list[DirectionalRule],
    ) -> list[Conflict]:
        """Detect conflicts among a set of directional rules.

        A conflict is raised when:
        - Two rules share identical priorities with contradictory constraints
        - Prohibited authorities overlap with allowed authorities
        - Conflict policy is ESCALATE_TO_GOVERNANCE and ambiguity exists
        """
        conflicts: list[Conflict] = []
        seen_pairs: set[tuple[str, str]] = set()

        for i, rule_a in enumerate(rules):
            for rule_b in rules[i + 1 :]:
                pair_key = tuple(sorted([rule_a.rule_id, rule_b.rule_id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                overlap_a = set(rule_a.prohibited_authorities) & set(
                    rule_b.allowed_authorities
                )
                overlap_b = set(rule_b.prohibited_authorities) & set(
                    rule_a.allowed_authorities
                )
                if overlap_a or overlap_b:
                    descriptions: list[str] = []
                    if overlap_a:
                        descriptions.append(
                            f"Rule {rule_a.rule_id} prohibits authorities "
                            f"that rule {rule_b.rule_id} allows: {sorted(overlap_a)}"
                        )
                    if overlap_b:
                        descriptions.append(
                            f"Rule {rule_b.rule_id} prohibits authorities "
                            f"that rule {rule_a.rule_id} allows: {sorted(overlap_b)}"
                        )
                    conflicts.append(
                        Conflict(
                            conflict_id=f"conflict-{rule_a.rule_id}-{rule_b.rule_id}",
                            rules_in_conflict=[rule_a.rule_id, rule_b.rule_id],
                            description="; ".join(descriptions),
                            severity="high",
                            governance_required=True,
                        )
                    )

        return conflicts

    def build_traceability(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> Traceability:
        """Build a traceability link between two artifacts."""
        return Traceability(
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
        )
