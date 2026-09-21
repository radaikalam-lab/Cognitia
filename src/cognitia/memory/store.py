"""Cognitia Memory Store Protocol and Reference Implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.abi.types import (
    Action,
    CognitiveObject,
    Decision,
    Observation,
    Outcome,
)
from cognitia.epistemic.types import Claim, EpistemicStatus, Evidence, Hypothesis
from cognitia.experience.record import ExperienceRecord
from cognitia.memory.types import MemoryContext, MemoryQuery
from cognitia.persistence.events import ObjectQuery
from cognitia.persistence.store import InMemoryPersistenceStore, PersistenceStore
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import ReasoningTrace


@runtime_checkable
class MemoryStore(Protocol):
    """Protocol for provider-agnostic cognitive memory retrieval."""

    def retrieve(self, query: MemoryQuery) -> list[CognitiveObject]:
        """Retrieve relevant persisted cognitive objects matching query dimensions."""
        ...

    def get_context(self, query: MemoryQuery) -> MemoryContext:
        """Assemble structured memory context retaining original entity identities and provenance."""
        ...


class InMemoryMemoryStore:
    """Read-oriented in-memory reference implementation of MemoryStore querying PersistenceStore."""

    def __init__(self, persistence_store: PersistenceStore | None = None) -> None:
        self._persistence: PersistenceStore = persistence_store or InMemoryPersistenceStore()

    @property
    def persistence(self) -> PersistenceStore:
        return self._persistence

    def retrieve(self, query: MemoryQuery) -> list[CognitiveObject]:
        all_objects = self._persistence.list_all_objects()
        results: list[CognitiveObject] = []

        for obj in all_objects:
            # Type filter
            if query.object_types:
                obj_type = type(obj).__name__.lower()
                if not any(t.lower() in obj_type for t in query.object_types):
                    continue

            # Time range filter
            if query.start_time and obj.created_at < query.start_time:
                continue
            if query.end_time and obj.created_at > query.end_time:
                continue

            # Experience and generic object filters
            if isinstance(obj, ExperienceRecord):
                if query.agent_id and obj.agent_id != query.agent_id:
                    continue
                if query.environment_id and obj.environment_id != query.environment_id:
                    continue
                if query.episode_id and obj.episode_id != query.episode_id:
                    continue
                if query.source_application and obj.source_application != query.source_application:
                    continue
                if query.model_version and obj.model_version != query.model_version:
                    continue
            else:
                meta = getattr(obj, "metadata", {})
                if isinstance(meta, dict):
                    if query.source_application and meta.get("source_application") and meta["source_application"] != query.source_application:
                        continue
                    if query.episode_id:
                        doc_name = meta.get("doc_name") or meta.get("episode_id")
                        if doc_name and doc_name != query.episode_id:
                            continue
                        elif not doc_name and not getattr(obj, "source_id", "").endswith(f":{query.episode_id}"):
                            continue

            # Metadata filters
            if query.metadata_filters and hasattr(obj, "metadata") and isinstance(obj.metadata, dict):
                match = True
                for mk, mv in query.metadata_filters.items():
                    if obj.metadata.get(mk) != mv:
                        match = False
                        break
                if not match:
                    continue

            # Epistemic status filter for claims/hypotheses
            if query.epistemic_status:
                if isinstance(obj, Claim) and obj.status != query.epistemic_status:
                    continue
                if isinstance(obj, Hypothesis) and obj.initial_status != query.epistemic_status:
                    continue

            results.append(obj)
            if query.limit and len(results) >= query.limit:
                break

        return results

    def get_context(self, query: MemoryQuery) -> MemoryContext:
        matched_objects = self.retrieve(query)

        experiences: list[ExperienceRecord] = []
        observations: list[Observation] = []
        evidence: list[Evidence] = []
        hypotheses: list[Hypothesis] = []
        claims: list[Claim] = []
        reasoning_traces: list[ReasoningTrace] = []
        decisions: list[Decision] = []
        outcomes: list[Outcome] = []
        epistemic_states: dict[str, EpistemicStatus] = {}
        parent_ids: list[str] = []

        for obj in matched_objects:
            parent_ids.append(obj.id)
            if isinstance(obj, ExperienceRecord):
                experiences.append(obj)
            elif isinstance(obj, Observation):
                observations.append(obj)
            elif isinstance(obj, Evidence):
                evidence.append(obj)
            elif isinstance(obj, Hypothesis):
                hypotheses.append(obj)
                epistemic_states[obj.id] = obj.initial_status
            elif isinstance(obj, Claim):
                claims.append(obj)
                epistemic_states[obj.id] = obj.status
            elif isinstance(obj, ReasoningTrace):
                reasoning_traces.append(obj)
            elif isinstance(obj, Decision):
                decisions.append(obj)
            elif isinstance(obj, Outcome):
                outcomes.append(obj)

        prov = ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id="memory_store",
            parent_ids=parent_ids,
            is_deterministic=True,
        )

        return MemoryContext(
            query=query,
            experiences=experiences,
            observations=observations,
            evidence=evidence,
            hypotheses=hypotheses,
            claims=claims,
            reasoning_traces=reasoning_traces,
            decisions=decisions,
            outcomes=outcomes,
            epistemic_states=epistemic_states,
            provenance=prov,
        )
