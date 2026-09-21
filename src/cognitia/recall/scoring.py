"""Cognitia Deterministic Recall Scoring.

Implements deterministic, offline, provider-independent scoring for cognitive recall.
No ML, embeddings, vector DB, or stochastic components are used.
"""

from __future__ import annotations

from typing import Any

from cognitia.memory.types import MemoryQuery
from cognitia.recall.types import (
    RecallCandidate,
    RecallObjectType,
    RecallQuery,
    RecallScore,
    ScoreComponent,
    ScoreComponentType,
)


class DeterministicRecallScoring:
    """Deterministic scoring profile for cognitive recall.

    Computes a composite RecallScore from discrete matching components.
    All scoring is offline, deterministic, and does not depend on
    external providers or learned representations.
    """

    def __init__(
        self,
        weight_temporal_recency: float = 0.25,
        weight_episode_match: float = 0.2,
        weight_agent_match: float = 0.15,
        weight_environment_match: float = 0.1,
        weight_epistemic_stability: float = 0.15,
        weight_source_application_match: float = 0.05,
        weight_metadata_match: float = 0.1,
    ) -> None:
        total = (
            weight_temporal_recency
            + weight_episode_match
            + weight_agent_match
            + weight_environment_match
            + weight_epistemic_stability
            + weight_source_application_match
            + weight_metadata_match
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"Recall scoring weights must sum to 1.0, got {total}"
            )

        self.weights = {
            ScoreComponentType.TEMPORAL_RECENCY: weight_temporal_recency,
            ScoreComponentType.EPISODE_MATCH: weight_episode_match,
            ScoreComponentType.AGENT_MATCH: weight_agent_match,
            ScoreComponentType.ENVIRONMENT_MATCH: weight_environment_match,
            ScoreComponentType.EPISTEMIC_STABILITY: weight_epistemic_stability,
            ScoreComponentType.SOURCE_APPLICATION_MATCH: weight_source_application_match,
            ScoreComponentType.METADATA_MATCH: weight_metadata_match,
        }

    def score_candidate(
        self,
        candidate: RecallCandidate,
        reference_time: str | None = None,
    ) -> RecallScore:
        """Compute a deterministic RecallScore for a RecallCandidate.

        Args:
            candidate: recall candidate to score.
            reference_time: ISO-8601 timestamp for temporal recency evaluation.
                Defaults to the query created_at.

        Returns:
            RecallScore with weighted components.
        """
        query = candidate.query
        obj = candidate.object
        ref_time = reference_time or query.created_at

        components = []

        components.append(
            self._score_temporal_recency(obj, ref_time)
        )
        components.append(
            self._score_episode_match(query, obj)
        )
        components.append(
            self._score_agent_match(query, obj)
        )
        components.append(
            self._score_environment_match(query, obj)
        )
        components.append(
            self._score_epistemic_stability(obj)
        )
        components.append(
            self._score_source_application_match(query, obj)
        )
        components.append(
            self._score_metadata_match(query, obj)
        )

        final_score = sum(component.weighted_value for component in components)
        max_score = 1.0

        return RecallScore(
            final_score=final_score,
            components=tuple(components),
            max_possible_score=max_score,
        )

    def _score_temporal_recency(
        self, obj: Any, reference_time: str
    ) -> ScoreComponent:
        """Score temporal proximity to reference time."""
        obj_time = getattr(obj, "created_at", reference_time)
        try:
            from datetime import datetime

            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            ref_dt = datetime.strptime(reference_time, fmt)
            obj_dt = datetime.strptime(obj_time, fmt)
            delta_seconds = abs((ref_dt - obj_dt).total_seconds())
        except Exception:
            delta_seconds = 0.0

        weight = self.weights[ScoreComponentType.TEMPORAL_RECENCY]
        raw_value = max(0.0, 1.0 / (1.0 + delta_seconds))
        weighted_value = weight * raw_value

        return ScoreComponent(
            component_type=ScoreComponentType.TEMPORAL_RECENCY,
            raw_value=raw_value,
            weight=weight,
            weighted_value=weighted_value,
        )

    def _score_episode_match(
        self, query: RecallQuery, obj: Any
    ) -> ScoreComponent:
        weight = self.weights[ScoreComponentType.EPISODE_MATCH]
        raw_value = 0.0

        if not query.episode_id:
            raw_value = 1.0
        else:
            from cognitia.memory.store import InMemoryMemoryStore
            store = InMemoryMemoryStore()
            memory_query = MemoryQuery(episode_id=query.episode_id)
            matched = store.retrieve(memory_query)
            if any(m.id == obj.id for m in matched):
                raw_value = 1.0

        return ScoreComponent(
            component_type=ScoreComponentType.EPISODE_MATCH,
            raw_value=raw_value,
            weight=weight,
            weighted_value=weight * raw_value,
        )

    def _score_agent_match(
        self, query: RecallQuery, obj: Any
    ) -> ScoreComponent:
        weight = self.weights[ScoreComponentType.AGENT_MATCH]
        raw_value = 0.0

        if not query.agent_id:
            raw_value = 1.0
        else:
            obj_agent = getattr(obj, "agent_id", None)
            if obj_agent == query.agent_id:
                raw_value = 1.0

        return ScoreComponent(
            component_type=ScoreComponentType.AGENT_MATCH,
            raw_value=raw_value,
            weight=weight,
            weighted_value=weight * raw_value,
        )

    def _score_environment_match(
        self, query: RecallQuery, obj: Any
    ) -> ScoreComponent:
        weight = self.weights[ScoreComponentType.ENVIRONMENT_MATCH]
        raw_value = 0.0

        if not query.environment_id:
            raw_value = 1.0
        else:
            obj_env = getattr(obj, "environment_id", None)
            if obj_env == query.environment_id:
                raw_value = 1.0

        return ScoreComponent(
            component_type=ScoreComponentType.ENVIRONMENT_MATCH,
            raw_value=raw_value,
            weight=weight,
            weighted_value=weight * raw_value,
        )

    def _score_epistemic_stability(self, obj: Any) -> ScoreComponent:
        weight = self.weights[ScoreComponentType.EPISTEMIC_STABILITY]
        raw_value = 0.0

        status = getattr(obj, "status", None)
        initial_status = getattr(obj, "initial_status", None)
        effective_status = status or initial_status

        if effective_status == "consolidated":
            raw_value = 1.0
        elif effective_status == "supported":
            raw_value = 0.75
        elif effective_status == "pending":
            raw_value = 0.5
        elif effective_status == "refuted":
            raw_value = 0.25
        elif effective_status == "rejected":
            raw_value = 0.0
        else:
            raw_value = 0.5

        return ScoreComponent(
            component_type=ScoreComponentType.EPISTEMIC_STABILITY,
            raw_value=raw_value,
            weight=weight,
            weighted_value=weight * raw_value,
        )

    def _score_source_application_match(
        self, query: RecallQuery, obj: Any
    ) -> ScoreComponent:
        weight = self.weights[ScoreComponentType.SOURCE_APPLICATION_MATCH]
        raw_value = 0.0

        if not query.source_application:
            raw_value = 1.0
        else:
            obj_source = getattr(obj, "source_application", None)
            if obj_source == query.source_application:
                raw_value = 1.0

        return ScoreComponent(
            component_type=ScoreComponentType.SOURCE_APPLICATION_MATCH,
            raw_value=raw_value,
            weight=weight,
            weighted_value=weight * raw_value,
        )

    def _score_metadata_match(
        self, query: RecallQuery, obj: Any
    ) -> ScoreComponent:
        weight = self.weights[ScoreComponentType.METADATA_MATCH]
        raw_value = 0.0

        if not query.metadata_filters:
            raw_value = 1.0
        else:
            meta = getattr(obj, "metadata", {})
            if isinstance(meta, dict):
                matches = sum(
                    1 for k, v in query.metadata_filters.items() if meta.get(k) == v
                )
                raw_value = matches / len(query.metadata_filters)

        return ScoreComponent(
            component_type=ScoreComponentType.METADATA_MATCH,
            raw_value=raw_value,
            weight=weight,
            weighted_value=weight * raw_value,
        )

    def score_candidates(
        self,
        candidates: list[RecallCandidate],
        reference_time: str | None = None,
    ) -> list[RecallScore]:
        """Score multiple candidates deterministically.

        Returns:
            List of RecallScore objects in the same order as candidates.
        """
        return [self.score_candidate(c, reference_time) for c in candidates]
