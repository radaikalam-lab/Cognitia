"""Cognitia Phase 10: Integrated Cognitive Loop Tests."""

from __future__ import annotations

import pytest

from cognitia.abi.types import Action, Observation, Outcome
from cognitia.attention.types import AttentionQuery
from cognitia.capabilities.base import DeterministicMockDecisionProvider
from cognitia.context.types import ContextQuery
from cognitia.documents.types import SectionType
from cognitia.epistemic.types import EpistemicStatus
from cognitia.integration.loop import DeterministicCognitiveLoop
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.persistence.events import CognitiveEventType, EventQuery
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.recall.types import RecallObjectType, RecallQuery


class TestCognitiveLoopExecution:
    def test_complete_cycle_produces_all_artifacts(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_1", "value": 42.0},
        )
        result = loop.execute(observation, episode_id="episode_1")
        assert result.observation_id == observation.id
        assert result.experience_id != ""
        assert result.reasoning_trace_id != ""
        assert result.decision_id is not None
        assert result.document_id is not None
        assert len(result.provenance_chain) > 0

    def test_complete_cycle_persists_canonical_artifacts(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_2", "value": 7.0},
        )
        result = loop.execute(observation, episode_id="episode_2")
        persisted_objects = store.list_all_objects()
        persisted_ids = [obj.id for obj in persisted_objects]
        assert result.observation_id in persisted_ids
        assert result.experience_id in persisted_ids
        assert result.reasoning_trace_id in persisted_ids
        assert result.decision_id in persisted_ids
        assert result.document_id in persisted_ids

    def test_complete_cycle_persists_events(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_3", "value": 13.0},
        )
        result = loop.execute(observation, episode_id="episode_3")
        all_events = store.get_timeline()
        event_types = {event.event_type for event in all_events}
        assert CognitiveEventType.OBSERVATION_RECORDED.value in event_types
        assert CognitiveEventType.EXPERIENCE_RECORDED.value in event_types

    def test_identity_boundaries_preserved(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_4", "value": 99.0},
        )
        result = loop.execute(observation, episode_id="episode_4")
        assert result.observation_id != result.experience_id
        assert result.observation_id != result.reasoning_trace_id
        assert result.observation_id != result.document_id
        if result.proposal_id:
            assert result.proposal_id != result.decision_id

    def test_document_is_projection_not_authority(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_5", "value": 1.0},
        )
        result = loop.execute(observation, episode_id="episode_5")
        doc = loop._documents.get_document(result.document_id)
        assert doc is not None
        assert not hasattr(doc, "execute")
        assert not hasattr(doc, "actuate")

    def test_decision_is_advisory_not_execution(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_6", "value": 2.0},
        )
        result = loop.execute(observation, episode_id="episode_6")
        decision = loop._decision.propose_decision(observation)
        assert not hasattr(decision, "execute")
        assert not hasattr(decision, "actuate")

    def test_outcome_feedback_extends_loop(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_7", "value": 3.0},
        )
        result = loop.execute(observation, episode_id="episode_7")
        outcome = Outcome(
            status="success",
            metrics={"value": 3.0},
        )
        updated = loop.accept_outcome(outcome, result, episode_id="episode_7")
        assert updated.provenance_chain[-1] == outcome.id
        retrieved = store.get_object(outcome.id)
        assert retrieved is not None
        assert retrieved.id == outcome.id


class TestCognitiveLoopMultiCycle:
    def test_second_cycle_retrieves_prior_history(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        obs_a = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_cycle", "value": 10.0},
        )
        result_a = loop.execute(obs_a, episode_id="multi_ep")
        recall_result = loop._recall.recall(
            RecallQuery(
                episode_id="multi_ep",
                object_types=(RecallObjectType.EXPERIENCE_RECORD,),
                limit=10,
            )
        )
        recalled_ids = [candidate.object.id for candidate in recall_result.candidates]
        assert result_a.experience_id in recalled_ids

    def test_multi_cycle_identity_independent(self) -> None:
        loop = DeterministicCognitiveLoop()
        obs_1 = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_multi", "value": 1.0},
        )
        obs_2 = Observation(
            source_id="test_sensor",
            payload={"subject_id": "subj_multi", "value": 2.0},
        )
        r1 = loop.execute(obs_1, episode_id="multi_2")
        r2 = loop.execute(obs_2, episode_id="multi_2")
        assert r1.observation_id != r2.observation_id
        assert r1.experience_id != r2.experience_id
        assert r1.reasoning_trace_id != r2.reasoning_trace_id


class TestCognitiveLoopContradictions:
    def test_contradictory_observations_preserved(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        obs_a = Observation(
            source_id="test_sensor",
            payload={"subject_id": "contradiction", "value": 1.0},
        )
        obs_b = Observation(
            source_id="test_sensor",
            payload={"subject_id": "contradiction", "value": 0.0},
        )
        loop.execute(obs_a, episode_id="contra_ep")
        loop.execute(obs_b, episode_id="contra_ep")
        objects = store.list_all_objects()
        observations = [obj for obj in objects if isinstance(obj, Observation)]
        values = [obs.payload.get("value") for obs in observations]
        assert 1.0 in values
        assert 0.0 in values


class TestCognitiveLoopFailureIsolation:
    def test_empty_observation_completes_cycle(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation()
        result = loop.execute(observation, episode_id="empty_ep")
        assert result.observation_id == observation.id
        assert result.experience_id != ""
        assert result.decision_id is not None
        assert result.document_id is not None

    def test_cycle_with_custom_decision_provider(self) -> None:
        custom = DeterministicMockDecisionProvider(
            capability_id="custom_decision",
            provider_name="custom_provider",
        )
        loop = DeterministicCognitiveLoop(decision_provider=custom)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "custom_dp", "value": 5.0},
        )
        result = loop.execute(observation, episode_id="custom_dp_ep")
        assert result.decision_id is not None
        decision = loop._decision.propose_decision(observation)
        assert decision.proposal_type == "deterministic_policy_proposal"


class TestCognitiveLoopProvenance:
    def test_provenance_chain_is_reconstructable(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "prov_chain", "value": 77.0},
        )
        result = loop.execute(observation, episode_id="prov_ep")
        chain = result.provenance_chain
        assert result.observation_id in chain
        assert result.experience_id in chain
        assert result.reasoning_trace_id in chain
        assert result.decision_id in chain
        assert result.document_id in chain

    def test_all_artifacts_have_provenance(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "prov_all", "value": 88.0},
        )
        result = loop.execute(observation, episode_id="prov_all_ep")
        for obj in store.list_all_objects():
            if isinstance(obj, Observation):
                continue
            assert hasattr(obj, "provenance"), f"{type(obj).__name__} missing provenance"
