"""Cognitia Project Directional Programming Service Interface and In-Memory Reference Implementation."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.project_spec.types import (
    ArchitectureCandidate,
    Conflict,
    DirectionalRule,
    DirectionalSpec,
    EvidenceRequest,
    Projection,
    ScaffoldSpec,
    Traceability,
)


@runtime_checkable
class ProjectSpecService(Protocol):
    """Protocol governing project directional specification, projection, and traceability."""

    def create_specification(
        self,
        rules: list[DirectionalRule],
        metadata: dict[str, Any] | None = None,
    ) -> DirectionalSpec: ...

    def get_specification(self, spec_id: str) -> DirectionalSpec | None: ...

    def list_specifications(self) -> list[DirectionalSpec]: ...

    def add_rule(self, spec_id: str, rule: DirectionalRule) -> DirectionalSpec: ...

    def create_architecture_candidate(
        self,
        spec_id: str,
        candidate: ArchitectureCandidate,
    ) -> ArchitectureCandidate: ...

    def get_architecture_candidate(self, candidate_id: str) -> ArchitectureCandidate | None: ...

    def create_scaffold_spec(
        self,
        candidate_id: str,
        scaffold: ScaffoldSpec,
    ) -> ScaffoldSpec: ...

    def get_scaffold_spec(self, spec_id: str) -> ScaffoldSpec | None: ...

    def create_projection(
        self,
        source_id: str,
        target_id: str,
        projection_type: str,
        source_references: list[str] | None = None,
        result_references: list[str] | None = None,
    ) -> Projection: ...

    def get_projection(self, projection_id: str) -> Projection | None: ...

    def create_evidence_request(
        self,
        rule_id: str,
        projection_id: str,
        evidence_type: str,
        acceptance_condition: str,
    ) -> EvidenceRequest: ...

    def create_conflict(
        self,
        rules_in_conflict: list[str],
        description: str,
        affected_projection: str = "",
        severity: str = "medium",
    ) -> Conflict: ...

    def add_traceability(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> Traceability: ...

    def get_traceability(self, source_id: str) -> list[Traceability]: ...

    def get_reverse_traceability(self, target_id: str) -> list[Traceability]: ...


class InMemoryProjectSpecService:
    """Thread-safe in-memory reference implementation of ProjectSpecService."""

    def __init__(self) -> None:
        self._specs: dict[str, DirectionalSpec] = {}
        self._rules: dict[str, DirectionalRule] = {}
        self._architecture_candidates: dict[str, ArchitectureCandidate] = {}
        self._scaffold_specs: dict[str, ScaffoldSpec] = {}
        self._projections: dict[str, Projection] = {}
        self._evidence_requests: dict[str, EvidenceRequest] = {}
        self._conflicts: dict[str, Conflict] = {}
        self._traceability: list[Traceability] = []
        self._spec_candidates: dict[str, list[str]] = {}
        self._candidate_scaffolds: dict[str, list[str]] = {}

    def create_specification(
        self,
        rules: list[DirectionalRule],
        metadata: dict[str, Any] | None = None,
    ) -> DirectionalSpec:
        spec = DirectionalSpec(rules=rules, metadata=metadata)
        self._specs[spec.id] = spec
        for rule in rules:
            self._rules[rule.rule_id or rule.id] = rule
        return spec

    def get_specification(self, spec_id: str) -> DirectionalSpec | None:
        return self._specs.get(spec_id)

    def list_specifications(self) -> list[DirectionalSpec]:
        return list(self._specs.values())

    def add_rule(self, spec_id: str, rule: DirectionalRule) -> DirectionalSpec:
        spec = self._specs.get(spec_id)
        if spec is None:
            raise KeyError(f"Specification '{spec_id}' not found")
        updated = DirectionalSpec(
            rules=spec.rules + (rule,),
            metadata=spec.metadata,
            provenance=spec.provenance,
        )
        self._specs[spec_id] = updated
        self._rules[rule.rule_id or rule.id] = rule
        return updated

    def create_architecture_candidate(
        self,
        spec_id: str,
        candidate: ArchitectureCandidate,
    ) -> ArchitectureCandidate:
        spec = self._specs.get(spec_id)
        if spec is None:
            raise KeyError(f"Specification '{spec_id}' not found")
        self._architecture_candidates[candidate.candidate_id or candidate.id] = candidate
        self._spec_candidates.setdefault(spec_id, []).append(
            candidate.candidate_id or candidate.id
        )
        return candidate

    def get_architecture_candidate(self, candidate_id: str) -> ArchitectureCandidate | None:
        return self._architecture_candidates.get(candidate_id)

    def create_scaffold_spec(
        self,
        candidate_id: str,
        scaffold: ScaffoldSpec,
    ) -> ScaffoldSpec:
        candidate = self._architecture_candidates.get(candidate_id)
        if candidate is None:
            raise KeyError(f"Architecture candidate '{candidate_id}' not found")
        self._scaffold_specs[scaffold.spec_id or scaffold.id] = scaffold
        self._candidate_scaffolds.setdefault(candidate_id, []).append(
            scaffold.spec_id or scaffold.id
        )
        return scaffold

    def get_scaffold_spec(self, spec_id: str) -> ScaffoldSpec | None:
        return self._scaffold_specs.get(spec_id)

    def create_projection(
        self,
        source_id: str,
        target_id: str,
        projection_type: str,
        source_references: list[str] | None = None,
        result_references: list[str] | None = None,
    ) -> Projection:
        projection = Projection(
            source_id=source_id,
            target_id=target_id,
            projection_type=projection_type,
            source_references=source_references or [],
            result_references=result_references or [],
        )
        self._projections[projection.id] = projection
        return projection

    def get_projection(self, projection_id: str) -> Projection | None:
        return self._projections.get(projection_id)

    def create_evidence_request(
        self,
        rule_id: str,
        projection_id: str,
        evidence_type: str,
        acceptance_condition: str,
    ) -> EvidenceRequest:
        request = EvidenceRequest(
            rule_id=rule_id,
            projection_id=projection_id,
            evidence_type=evidence_type,
            acceptance_condition=acceptance_condition,
        )
        self._evidence_requests[request.id] = request
        return request

    def create_conflict(
        self,
        rules_in_conflict: list[str],
        description: str,
        affected_projection: str = "",
        severity: str = "medium",
    ) -> Conflict:
        conflict = Conflict(
            rules_in_conflict=rules_in_conflict,
            description=description,
            affected_projection=affected_projection,
            severity=severity,
        )
        self._conflicts[conflict.id] = conflict
        return conflict

    def add_traceability(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> Traceability:
        link = Traceability(
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
        )
        self._traceability.append(link)
        return link

    def get_traceability(self, source_id: str) -> list[Traceability]:
        return [link for link in self._traceability if link.source_id == source_id]

    def get_reverse_traceability(self, target_id: str) -> list[Traceability]:
        return [link for link in self._traceability if link.target_id == target_id]
