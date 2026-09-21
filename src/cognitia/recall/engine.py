"""Cognitia Cognitive Recall Engine.

Provides deterministic, offline, read-only recall over cognitive objects
persisted in the PersistenceStore. Recall is provider-independent and
snapshot-safe. It does not perform attention, reasoning, learning, truth
evaluation, or causality inference.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import CognitiveObject
from cognitia.epistemic.types import EpistemicStatus
from cognitia.memory.store import InMemoryMemoryStore, MemoryStore
from cognitia.persistence.store import (
    InMemoryPersistenceStore,
    ObjectQuery,
    PersistenceStore,
)
from cognitia.recall.scoring import DeterministicRecallScoring
from cognitia.recall.types import (
    RecallCandidate,
    RecallObjectType,
    RecallQuery,
    RecallResult,
    RecallScore,
    RecallTrace,
    RelevanceReason,
)


@runtime_checkable
class RecallEngine(Protocol):
    """Protocol for provider-agnostic cognitive recall."""

    def recall(self, query: RecallQuery) -> RecallResult:
        """Execute deterministic recall and return ranked results."""
        ...

    def recall_with_trace(self, query: RecallQuery) -> tuple[RecallResult, RecallTrace]:
        """Execute recall and return both results and execution trace."""
        ...


class InMemoryRecallEngine:
    """Deterministic, in-memory reference implementation of RecallEngine.

    Reads cognitive objects from a PersistenceStore and ranks them according
    to deterministic scoring. No external providers, embeddings, or learned
    models are used.
    """

    def __init__(
        self,
        persistence_store: PersistenceStore | None = None,
        memory_store: MemoryStore | None = None,
        scoring: DeterministicRecallScoring | None = None,
        engine_id: str = "in_memory_recall_engine",
    ) -> None:
        self._persistence = persistence_store or InMemoryPersistenceStore()
        self._memory_store = memory_store or InMemoryMemoryStore(self._persistence)
        self._scoring = scoring or DeterministicRecallScoring()
        self._engine_id = engine_id

    @property
    def persistence(self) -> PersistenceStore:
        return self._persistence

    @property
    def memory_store(self) -> MemoryStore:
        return self._memory_store

    @property
    def scoring(self) -> DeterministicRecallScoring:
        return self._scoring

    def recall(self, query: RecallQuery) -> RecallResult:
        """Execute deterministic recall and return ranked results.

        Args:
            query: recall query dimensions.

        Returns:
            RecallResult with ranked candidates and provenance metadata.
        """
        result, _ = self.recall_with_trace(query)
        return result

    def recall_with_trace(
        self, query: RecallQuery
    ) -> tuple[RecallResult, RecallTrace]:
        """Execute recall and return both results and execution trace.

        Returns:
            Tuple of (RecallResult, RecallTrace).
        """
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        candidates = self._evaluate_candidates(query)
        scored = self._score_candidates(query, candidates)
        ranked = self._rank_candidates(scored)

        total_evaluated = len(candidates)
        total_matched = len(scored)
        limit = query.limit
        truncated = False
        returned = ranked

        if limit is not None and total_matched > limit:
            returned = ranked[:limit]
            truncated = True

        candidates_tuple = tuple(
            self._attach_rank(c, index + 1)
            for index, c in enumerate(returned)
        )

        completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        result = RecallResult(
            query=query,
            candidates=candidates_tuple,
            total_evaluated=total_evaluated,
            total_matched=total_matched,
            truncated=truncated,
            trace_id=query.query_id,
        )

        trace = RecallTrace(
            trace_id=query.query_id,
            query=query,
            engine_id=self._engine_id,
            total_evaluated=total_evaluated,
            total_matched=total_matched,
            returned_count=len(candidates_tuple),
            truncated=truncated,
            started_at=started_at,
            completed_at=completed_at,
        )

        return result, trace

    def _evaluate_candidates(self, query: RecallQuery) -> list[CognitiveObject]:
        """Evaluate candidates from persistence store matching recall filters."""
        all_objects = self._persistence.list_all_objects()
        matched: list[CognitiveObject] = []

        object_type_names = {t.value for t in query.object_types}

        for obj in all_objects:
            if object_type_names:
                obj_type_name = type(obj).__name__.lower().replace("_", "")
                if not any(name.replace("_", "") in obj_type_name for name in object_type_names):
                    continue

            if query.agent_id:
                obj_agent = getattr(obj, "agent_id", None)
                if obj_agent != query.agent_id:
                    continue

            if query.environment_id:
                obj_env = getattr(obj, "environment_id", None)
                if obj_env != query.environment_id:
                    continue

            if query.episode_id:
                obj_episode = getattr(obj, "episode_id", None)
                if obj_episode != query.episode_id:
                    continue

            if query.source_application:
                obj_source = getattr(obj, "source_application", None)
                if obj_source != query.source_application:
                    continue

            if query.model_version:
                obj_model = getattr(obj, "model_version", None)
                if obj_model != query.model_version:
                    continue

            if query.start_time and getattr(obj, "created_at", "") < query.start_time:
                continue

            if query.end_time and getattr(obj, "created_at", "") > query.end_time:
                continue

            if query.epistemic_statuses:
                obj_status = getattr(obj, "status", None) or getattr(
                    obj, "initial_status", None
                )
                if obj_status not in query.epistemic_statuses:
                    continue

            if query.metadata_filters:
                meta = getattr(obj, "metadata", {})
                if not isinstance(meta, dict):
                    continue
                if not all(meta.get(k) == v for k, v in query.metadata_filters.items()):
                    continue

            matched.append(obj)

        return matched

    def _score_candidates(
        self, query: RecallQuery, candidates: list[CognitiveObject]
    ) -> list[RecallCandidate]:
        """Wrap candidates in RecallCandidate and score them."""
        wrapped = [
            RecallCandidate(
                query=query,
                object=obj,
                score=RecallScore(final_score=0.0),
                relevance_reason=RelevanceReason.MEMORY_MATCH,
            )
            for obj in candidates
        ]

        scored = []
        for candidate in wrapped:
            score = self._scoring.score_candidate(candidate)
            scored.append(
                RecallCandidate(
                    query=candidate.query,
                    object=candidate.object,
                    score=score,
                    relevance_reason=candidate.relevance_reason,
                    matched_filters=candidate.matched_filters,
                    rank=candidate.rank,
                )
            )
        return scored

    def _rank_candidates(
        self, candidates: list[RecallCandidate]
    ) -> list[RecallCandidate]:
        """Rank candidates deterministically by score then object id."""

        def sort_key(c: RecallCandidate) -> tuple[float, str]:
            return (-c.score.normalized_score, c.object.id)

        return sorted(candidates, key=sort_key)

    def _attach_rank(
        self, candidate: RecallCandidate, rank: int
    ) -> RecallCandidate:
        """Attach rank to candidate."""
        return RecallCandidate(
            query=candidate.query,
            object=candidate.object,
            score=candidate.score,
            relevance_reason=candidate.relevance_reason,
            matched_filters=candidate.matched_filters,
            rank=rank,
        )
