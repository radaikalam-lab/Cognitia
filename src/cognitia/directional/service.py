"""Cognitia Directional Programming Service Interface and In-Memory Reference Implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.abi.types import CognitiveObject
from cognitia.directional.types import (
    DirectionalProposal,
    DirectionalSpecification,
)
from cognitia.persistence.store import PersistenceStore


@runtime_checkable
class DirectionalService(Protocol):
    """Protocol governing directional specification creation, persistence, and proposal generation."""

    def create_specification(
        self,
        objectives: list[object],
        constraints: list[object] | None = None,
        success_criteria: list[object] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> DirectionalSpecification: ...

    def get_specification(self, specification_id: str) -> DirectionalSpecification | None: ...

    def list_specifications(self) -> list[DirectionalSpecification]: ...

    def propose(
        self,
        specification_id: str,
        provider_id: str,
        provider_version: str = "1.0.0",
    ) -> DirectionalProposal: ...

    def get_proposal(self, proposal_id: str) -> DirectionalProposal | None: ...

    def list_proposals(self, specification_id: str | None = None) -> list[DirectionalProposal]: ...


class InMemoryDirectionalService:
    """Thread-safe in-memory reference implementation of DirectionalService."""

    def __init__(self, persistence_store: PersistenceStore | None = None) -> None:
        self._specifications: dict[str, DirectionalSpecification] = {}
        self._proposals: dict[str, DirectionalProposal] = {}
        self._proposals_by_spec: dict[str, list[str]] = {}
        self._persistence_store = persistence_store

    def create_specification(
        self,
        objectives: list[object],
        constraints: list[object] | None = None,
        success_criteria: list[object] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> DirectionalSpecification:
        spec = DirectionalSpecification(
            objectives=objectives,
            constraints=constraints or [],
            success_criteria=success_criteria or [],
            metadata=metadata,
        )
        self._specifications[spec.id] = spec
        if self._persistence_store:
            self._persistence_store.save_object(spec)
            for obj in spec.objectives:
                self._persistence_store.save_object(obj)
            for constraint in spec.constraints:
                self._persistence_store.save_object(constraint)
            for criterion in spec.success_criteria:
                self._persistence_store.save_object(criterion)
        return spec

    def get_specification(self, specification_id: str) -> DirectionalSpecification | None:
        return self._specifications.get(specification_id)

    def list_specifications(self) -> list[DirectionalSpecification]:
        return list(self._specifications.values())

    def propose(
        self,
        specification_id: str,
        provider_id: str,
        provider_version: str = "1.0.0",
    ) -> DirectionalProposal:
        spec = self._specifications.get(specification_id)
        if spec is None:
            raise KeyError(f"Specification '{specification_id}' not found")

        from cognitia.directional.provider import DeterministicDirectionalProvider
        provider = DeterministicDirectionalProvider(
            provider_id=provider_id,
            provider_version=provider_version,
        )
        proposal = provider.propose(spec)

        self._proposals[proposal.id] = proposal
        if specification_id not in self._proposals_by_spec:
            self._proposals_by_spec[specification_id] = []
        self._proposals_by_spec[specification_id].append(proposal.id)

        if self._persistence_store:
            self._persistence_store.save_object(proposal)
            for residual in proposal.residuals:
                self._persistence_store.save_object(residual)

        return proposal

    def get_proposal(self, proposal_id: str) -> DirectionalProposal | None:
        return self._proposals.get(proposal_id)

    def list_proposals(self, specification_id: str | None = None) -> list[DirectionalProposal]:
        if specification_id is None:
            return list(self._proposals.values())
        proposal_ids = self._proposals_by_spec.get(specification_id, [])
        return [self._proposals[pid] for pid in proposal_ids if pid in self._proposals]
