"""Cognitia Project Directional Programming Projection Service.

Implements the governed projection chain:

    DirectionalSpec
           ↓
    ArchitectureCandidate
           ↓
    ScaffoldSpec
           ↓
    ProjectionResult / Projection / Traceability

Projection is advisory/specification-producing infrastructure.
It does not approve, validate, or generate implementation code.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.project_spec.types import (
    ArchitectureCandidate,
    Conflict,
    DirectionalRule,
    DirectionalSpec,
    InteractionContract,
    Projection,
    ProjectionResult,
    ProjectionType,
    RelationshipType,
    ScaffoldSpec,
    Traceability,
)
from cognitia.project_spec.provider import (
    DeterministicProjectionProvider,
    ProjectionProvider,
)


@runtime_checkable
class ProjectionService(Protocol):
    """Protocol governing directional projection into architecture and scaffold."""

    def project(
        self,
        specification: DirectionalSpec,
    ) -> ProjectionResult: ...


class InMemoryProjectionService:
    """Deterministic in-memory projection service.

    Composes a ProjectionProvider with traceability generation to produce
    a complete ProjectionResult from a DirectionalSpec.

    This service contains no AI/ML/network/filesystem dependencies.
    It does not perform validation, governance, or code generation.
    """

    def __init__(
        self,
        provider: ProjectionProvider | None = None,
    ) -> None:
        self._provider = provider or DeterministicProjectionProvider()

    def project(
        self,
        specification: DirectionalSpec,
    ) -> ProjectionResult:
        """Project a DirectionalSpec into architecture and scaffold candidates.

        Returns a ProjectionResult containing:
        - architecture_candidate
        - scaffold_spec
        - projection records
        - traceability links
        - detected conflicts

        The result is a candidate artifact, not an accepted structure.
        """
        projections: list[Projection] = []
        traceability_links: list[Traceability] = []
        all_architecture_candidates: list[ArchitectureCandidate] = []
        scaffold: ScaffoldSpec | None = None
        conflicts: list[Conflict] = []
        all_technology_freedoms: list[str] = []
        all_interaction_contracts: list[InteractionContract] = []

        rules = list(specification.rules)

        conflicts = self._provider.detect_conflicts(rules)

        for rule in rules:
            rule_id = rule.rule_id or rule.id

            candidate = self._provider.project_rule_to_architecture(rule)
            all_architecture_candidates.append(candidate)

            projections.append(
                Projection(
                    source_id=rule_id,
                    target_id=candidate.candidate_id or candidate.id,
                    projection_type=ProjectionType.RULE_TO_ARCHITECTURE.value,
                    source_references=[rule_id],
                    result_references=[candidate.candidate_id or candidate.id],
                )
            )

            traceability_links.append(
                Traceability(
                    source_id=rule_id,
                    target_id=candidate.candidate_id or candidate.id,
                    relationship=RelationshipType.DERIVES.value,
                )
            )

            all_technology_freedoms.extend(rule.technology_freedoms)
            all_interaction_contracts.extend(rule.interaction_contracts)

        if all_architecture_candidates:
            merged_candidate = self._merge_architecture_candidates(
                all_architecture_candidates
            )
            scaffold = self._provider.project_architecture_to_scaffold(
                merged_candidate
            )

            unique_freedoms = sorted(set(all_technology_freedoms))
            scaffold = ScaffoldSpec(
                spec_id=scaffold.spec_id,
                required_boundaries=scaffold.required_boundaries,
                required_surfaces=scaffold.required_surfaces,
                required_interfaces=scaffold.required_interfaces,
                required_contract_surfaces=scaffold.required_contract_surfaces,
                required_test_surfaces=scaffold.required_test_surfaces,
                prohibited_structural_patterns=scaffold.prohibited_structural_patterns,
                implementation_freedoms=tuple(
                    sorted(set(scaffold.implementation_freedoms + tuple(unique_freedoms)))
                ),
                interaction_contracts=tuple(
                    contract.contract_id or contract.id
                    for contract in all_interaction_contracts
                ),
                traceability=scaffold.traceability,
                provenance=scaffold.provenance,
                metadata=scaffold.metadata,
            )

            projections.append(
                Projection(
                    source_id=merged_candidate.candidate_id or merged_candidate.id,
                    target_id=scaffold.spec_id or scaffold.id,
                    projection_type=ProjectionType.ARCHITECTURE_TO_SCAFFOLD.value,
                    source_references=[merged_candidate.candidate_id or merged_candidate.id],
                    result_references=[scaffold.spec_id or scaffold.id],
                )
            )

            traceability_links.append(
                Traceability(
                    source_id=merged_candidate.candidate_id or merged_candidate.id,
                    target_id=scaffold.spec_id or scaffold.id,
                    relationship=RelationshipType.IMPLEMENTS.value,
                )
            )

        for rule in rules:
            rule_id = rule.rule_id or rule.id
            if scaffold is not None:
                traceability_links.append(
                    Traceability(
                        source_id=rule_id,
                        target_id=scaffold.spec_id or scaffold.id,
                        relationship=RelationshipType.REQUIRES.value,
                    )
                )

        return ProjectionResult(
            specification_id=specification.id,
            architecture_candidate=merged_candidate if all_architecture_candidates else None,
            scaffold_spec=scaffold,
            projections=projections,
            traceability=traceability_links,
            conflicts=conflicts,
        )

    def _merge_architecture_candidates(
        self,
        candidates: list[ArchitectureCandidate],
    ) -> ArchitectureCandidate:
        """Merge multiple architecture candidates into a single candidate.

        Merging rules:
        - boundaries: union, deduplicated, sorted
        - authorities: union, deduplicated, sorted
        - responsibilities: union, deduplicated, sorted
        - dependencies: union, deduplicated, sorted
        - invariants: union, deduplicated, sorted
        - required_capabilities: union, deduplicated, sorted
        - prohibited_dependencies: union, deduplicated, sorted
        - observables: union, deduplicated, sorted
        - validation_requirements: union, deduplicated, sorted
        - interaction_contracts: union, deduplicated, sorted
        - traceability: union, deduplicated, sorted
        """
        merged_boundaries: list[str] = []
        merged_authorities: list[str] = []
        merged_responsibilities: list[str] = []
        merged_dependencies: list[str] = []
        merged_invariants: list[str] = []
        merged_required_capabilities: list[str] = []
        merged_prohibited_dependencies: list[str] = []
        merged_observables: list[str] = []
        merged_validation_requirements: list[str] = []
        merged_interaction_contracts: list[str] = []
        merged_traceability: list[str] = []

        all_ids: list[str] = []
        for candidate in candidates:
            merged_boundaries.extend(candidate.boundaries)
            merged_authorities.extend(candidate.authorities)
            merged_responsibilities.extend(candidate.responsibilities)
            merged_dependencies.extend(candidate.dependencies)
            merged_invariants.extend(candidate.invariants)
            merged_required_capabilities.extend(candidate.required_capabilities)
            merged_prohibited_dependencies.extend(candidate.prohibited_dependencies)
            merged_observables.extend(candidate.observables)
            merged_validation_requirements.extend(candidate.validation_requirements)
            merged_interaction_contracts.extend(candidate.interaction_contracts)
            merged_traceability.extend(candidate.traceability)
            all_ids.append(candidate.candidate_id or candidate.id)

        return ArchitectureCandidate(
            candidate_id=f"merged-{'-'.join(all_ids)}" if all_ids else "",
            boundaries=sorted(set(merged_boundaries)),
            authorities=sorted(set(merged_authorities)),
            responsibilities=sorted(set(merged_responsibilities)),
            dependencies=sorted(set(merged_dependencies)),
            invariants=sorted(set(merged_invariants)),
            required_capabilities=sorted(set(merged_required_capabilities)),
            prohibited_dependencies=sorted(set(merged_prohibited_dependencies)),
            observables=sorted(set(merged_observables)),
            validation_requirements=sorted(set(merged_validation_requirements)),
            interaction_contracts=sorted(set(merged_interaction_contracts)),
            traceability=sorted(set(merged_traceability)),
        )
