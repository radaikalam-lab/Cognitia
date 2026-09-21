"""Tests for Cognitia Cognitive Recall Module."""

from __future__ import annotations

import pytest

from cognitia.abi.types import Observation, Outcome
from cognitia.epistemic.types import Claim, EpistemicStatus, Evidence, Hypothesis
from cognitia.experience.record import ExperienceRecord, ExperienceBuilder
from cognitia.memory.consolidation import ConsolidationStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import ReasoningInput, ReasoningMode, ReasoningResult, ReasoningTrace
from cognitia.recall.engine import InMemoryRecallEngine
from cognitia.recall.scoring import DeterministicRecallScoring
from cognitia.recall.types import (
    RecallCandidate,
    RecallObjectType,
    RecallQuery,
    RecallResult,
    RecallScore,
    RecallTrace,
    RelevanceReason,
    ScoreComponent,
    ScoreComponentType,
)
from cognitia.persistence.store import InMemoryPersistenceStore


@pytest.fixture
def persistence_store() -> InMemoryPersistenceStore:
    return InMemoryPersistenceStore()


@pytest.fixture
def engine(persistence_store: InMemoryPersistenceStore) -> InMemoryRecallEngine:
    return InMemoryRecallEngine(persistence_store=persistence_store)


@pytest.fixture
def experience_factory(persistence_store: InMemoryPersistenceStore):
    def _create_experience(
        episode_id: str = "episode_1",
        agent_id: str = "agent_0",
        environment_id: str = "default_env",
        source_application: str = "test_app",
        model_version: str = "1.0.0",
        metadata: dict | None = None,
    ) -> ExperienceRecord:
        exp = (
            ExperienceBuilder(source_application=source_application, episode_id=episode_id)
            .with_agent(agent_id)
            .with_environment(environment_id)
            .with_model_version(model_version)
            .build()
        )
        if metadata:
            exp.metadata.update(metadata)
        persistence_store.save_object(exp)
        return exp

    return _create_experience


class TestRecallScore:
    def test_valid_score(self) -> None:
        score = RecallScore(final_score=0.8)
        assert score.final_score == 0.8
        assert score.normalized_score == 0.8

    def test_score_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            RecallScore(final_score=1.5)

    def test_score_normalized(self) -> None:
        score = RecallScore(final_score=0.5, max_possible_score=2.0)
        assert abs(score.normalized_score - 0.25) < 1e-9

    def test_zero_max_score_raises(self) -> None:
        with pytest.raises(ValueError):
            RecallScore(final_score=0.0, max_possible_score=0.0)

    def test_score_component_negative_weight_raises(self) -> None:
        with pytest.raises(ValueError):
            ScoreComponent(
                component_type=ScoreComponentType.AGENT_MATCH,
                raw_value=1.0,
                weight=-0.1,
                weighted_value=-0.1,
            )


class TestRecallQuery:
    def test_default_query(self) -> None:
        query = RecallQuery()
        assert query.query_id
        assert query.limit is None

    def test_query_with_object_types(self) -> None:
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
        )
        assert RecallObjectType.EXPERIENCE_RECORD in query.object_types

    def test_query_with_metadata_filters(self) -> None:
        query = RecallQuery(metadata_filters={"key": "value"})
        assert query.metadata_filters["key"] == "value"


class TestRecallCandidate:
    def test_candidate_requires_non_negative_rank(self) -> None:
        query = RecallQuery()
        score = RecallScore(final_score=0.5)
        with pytest.raises(ValueError):
            RecallCandidate(
                query=query,
                object=Observation(),
                score=score,
                relevance_reason=RelevanceReason.MEMORY_MATCH,
                rank=-1,
            )


class TestRecallResult:
    def test_result_truncated_without_candidates_raises(self) -> None:
        query = RecallQuery(limit=1)
        score = RecallScore(final_score=0.5)
        with pytest.raises(ValueError):
            RecallResult(
                query=query,
                candidates=(),
                total_evaluated=1,
                total_matched=1,
                truncated=True,
            )

    def test_result_limit_exceeded_raises(self) -> None:
        query = RecallQuery(limit=1)
        score = RecallScore(final_score=0.5)
        cand = RecallCandidate(
            query=query, object=Observation(), score=score, relevance_reason=RelevanceReason.MEMORY_MATCH
        )
        with pytest.raises(ValueError):
            RecallResult(
                query=query,
                candidates=(cand, cand),
                total_evaluated=2,
                total_matched=2,
                truncated=False,
            )

    def test_result_matched_exceeds_evaluated_raises(self) -> None:
        query = RecallQuery()
        score = RecallScore(final_score=0.5)
        cand = RecallCandidate(
            query=query, object=Observation(), score=score, relevance_reason=RelevanceReason.MEMORY_MATCH
        )
        with pytest.raises(ValueError):
            RecallResult(
                query=query,
                candidates=(cand,),
                total_evaluated=0,
                total_matched=1,
                truncated=False,
            )


class TestRecallTrace:
    def test_valid_trace(self) -> None:
        query = RecallQuery()
        trace = RecallTrace(query=query, total_evaluated=1, total_matched=1, returned_count=1)
        assert trace.engine_id == "default_recall_engine"

    def test_matched_exceeds_evaluated_raises(self) -> None:
        with pytest.raises(ValueError):
            RecallTrace(total_evaluated=1, total_matched=2, returned_count=1)

    def test_returned_exceeds_matched_raises(self) -> None:
        with pytest.raises(ValueError):
            RecallTrace(total_evaluated=2, total_matched=2, returned_count=3)

    def test_truncated_with_unreturned_allowed(self) -> None:
        trace = RecallTrace(total_evaluated=2, total_matched=2, returned_count=1, truncated=True)
        assert trace.truncated is True
        assert trace.returned_count == 1
        assert trace.total_matched == 2

    def test_completed_before_started_raises(self) -> None:
        with pytest.raises(ValueError):
            RecallTrace(
                started_at="2026-01-02T00:00:00.000Z",
                completed_at="2026-01-01T00:00:00.000Z",
            )


class TestDeterministicRecallScoring:
    def test_default_weights_sum_to_one(self) -> None:
        scoring = DeterministicRecallScoring()
        total = sum(scoring.weights.values())
        assert abs(total - 1.0) < 1e-9

    def test_invalid_weights_raise(self) -> None:
        with pytest.raises(ValueError):
            DeterministicRecallScoring(
                weight_temporal_recency=1.5,
                weight_episode_match=0.0,
                weight_agent_match=0.0,
                weight_environment_match=0.0,
                weight_epistemic_stability=0.0,
                weight_source_application_match=0.0,
                weight_metadata_match=0.0,
            )

    def test_score_bounds(self, engine: InMemoryRecallEngine, experience_factory) -> None:
        exp = experience_factory()
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        candidate = RecallCandidate(
            query=query,
            object=exp,
            score=RecallScore(final_score=0.0),
            relevance_reason=RelevanceReason.MEMORY_MATCH,
        )
        score = engine.scoring.score_candidate(candidate)
        assert 0.0 <= score.final_score <= 1.0

    def test_score_with_empty_query(self, engine: InMemoryRecallEngine, experience_factory) -> None:
        exp = experience_factory()
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        candidate = RecallCandidate(
            query=query,
            object=exp,
            score=RecallScore(final_score=0.0),
            relevance_reason=RelevanceReason.MEMORY_MATCH,
        )
        score = engine.scoring.score_candidate(candidate)
        assert score.normalized_score >= 0.0

    def test_score_deterministic(self, engine: InMemoryRecallEngine, experience_factory) -> None:
        exp = experience_factory()
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        candidate = RecallCandidate(
            query=query,
            object=exp,
            score=RecallScore(final_score=0.0),
            relevance_reason=RelevanceReason.MEMORY_MATCH,
        )
        first = engine.scoring.score_candidate(candidate)
        second = engine.scoring.score_candidate(candidate)
        assert first.final_score == second.final_score


class TestRecallEngine:
    def test_empty_recall(self, engine: InMemoryRecallEngine) -> None:
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        result = engine.recall(query)
        assert len(result.candidates) == 0
        assert result.total_evaluated == 0

    def test_recall_returns_ordered_results(
        self, engine: InMemoryRecallEngine, experience_factory
    ) -> None:
        exp1 = experience_factory(episode_id="episode_a")
        exp2 = experience_factory(episode_id="episode_b")
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            limit=2,
        )
        result = engine.recall(query)
        assert result.total_evaluated >= 2
        assert len(result.candidates) == 2
        scores = [c.score.normalized_score for c in result.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_recall_limit_enforced(self, engine: InMemoryRecallEngine, experience_factory) -> None:
        for _ in range(5):
            experience_factory()
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            limit=2,
        )
        result = engine.recall(query)
        assert len(result.candidates) <= 2
        if result.truncated:
            assert len(result.candidates) == 2

    def test_recall_provenance_present(self, engine: InMemoryRecallEngine) -> None:
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        result = engine.recall(query)
        assert result.provenance.source_type == SourceType.DETERMINISTIC_RULE
        assert result.provenance.producer_id == "recall_engine"

    def test_recall_with_episode_filter(
        self, engine: InMemoryRecallEngine, experience_factory
    ) -> None:
        experience_factory(episode_id="episode_target")
        experience_factory(episode_id="episode_other")
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            episode_id="episode_target",
        )
        result = engine.recall(query)
        for candidate in result.candidates:
            assert getattr(candidate.object, "episode_id", None) == "episode_target"

    def test_recall_with_agent_filter(
        self, engine: InMemoryRecallEngine, experience_factory
    ) -> None:
        experience_factory(agent_id="agent_1")
        experience_factory(agent_id="agent_2")
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            agent_id="agent_1",
        )
        result = engine.recall(query)
        for candidate in result.candidates:
            assert getattr(candidate.object, "agent_id", None) == "agent_1"

    def test_recall_with_environment_filter(
        self, engine: InMemoryRecallEngine, experience_factory
    ) -> None:
        experience_factory(environment_id="env_a")
        experience_factory(environment_id="env_b")
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            environment_id="env_a",
        )
        result = engine.recall(query)
        for candidate in result.candidates:
            assert getattr(candidate.object, "environment_id", None) == "env_a"

    def test_recall_with_source_application_filter(
        self, engine: InMemoryRecallEngine, experience_factory
    ) -> None:
        experience_factory(source_application="app_a")
        experience_factory(source_application="app_b")
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            source_application="app_a",
        )
        result = engine.recall(query)
        for candidate in result.candidates:
            assert getattr(candidate.object, "source_application", None) == "app_a"

    def test_recall_with_metadata_filter(
        self, engine: InMemoryRecallEngine, experience_factory
    ) -> None:
        experience_factory(metadata={"category": "alpha"})
        experience_factory(metadata={"category": "beta"})
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            metadata_filters={"category": "alpha"},
        )
        result = engine.recall(query)
        for candidate in result.candidates:
            meta = getattr(candidate.object, "metadata", {})
            assert meta.get("category") == "alpha"

    def test_recall_with_trace(self, engine: InMemoryRecallEngine, experience_factory) -> None:
        experience_factory()
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        result, trace = engine.recall_with_trace(query)
        assert trace.query == query
        assert trace.engine_id == engine._engine_id
        assert trace.returned_count == len(result.candidates)

    def test_recall_trace_consistency(self, engine: InMemoryRecallEngine, experience_factory) -> None:
        experience_factory()
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        result, trace = engine.recall_with_trace(query)
        assert trace.total_evaluated == result.total_evaluated
        assert trace.total_matched == result.total_matched
        assert trace.returned_count == len(result.candidates)

    def test_recall_result_candidate_rank(
        self, engine: InMemoryRecallEngine, experience_factory
    ) -> None:
        for _ in range(3):
            experience_factory()
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            limit=3,
        )
        result = engine.recall(query)
        ranks = [c.rank for c in result.candidates if c.rank is not None]
        assert ranks == sorted(ranks)
