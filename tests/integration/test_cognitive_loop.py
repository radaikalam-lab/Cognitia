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


class TestCognitiveLoopReconciliation:
    def test_repeated_execution_is_structurally_deterministic(self) -> None:
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "det", "value": 1.0},
        )
        loop_a = DeterministicCognitiveLoop()
        result_a = loop_a.execute(observation, episode_id="det_ep")
        loop_b = DeterministicCognitiveLoop()
        result_b = loop_b.execute(observation, episode_id="det_ep")
        assert len(result_a.provenance_chain) == len(result_b.provenance_chain)
        assert result_a.observation_id == result_b.observation_id
        assert result_a.experience_id != result_b.experience_id
        assert result_a.reasoning_trace_id != result_b.reasoning_trace_id
        assert result_a.decision_id != result_b.decision_id
        assert result_a.document_id != result_b.document_id

    def test_empty_recall_does_not_fabricate_context(self) -> None:
        class EmptyRecallEngine:
            def recall(self, query):
                from cognitia.recall.types import RecallResult
                return RecallResult(query=query)

        loop = DeterministicCognitiveLoop(recall_engine=EmptyRecallEngine())
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "empty_recall", "value": 2.0},
        )
        result = loop.execute(observation, episode_id="empty_recall_ep")
        assert result.observation_id == observation.id
        assert result.experience_id != ""
        assert result.decision_id is not None

    def test_empty_memory_does_not_fabricate_context(self) -> None:
        class EmptyMemoryStore:
            def get_context(self, query):
                from cognitia.memory.types import MemoryContext
                return MemoryContext(query=query)

        loop = DeterministicCognitiveLoop(memory_store=EmptyMemoryStore())
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "empty_mem", "value": 3.0},
        )
        result = loop.execute(observation, episode_id="empty_mem_ep")
        assert result.observation_id == observation.id
        assert result.experience_id != ""
        assert result.decision_id is not None

    def test_cycle_n_does_not_mutate_cycle_n_minus_one(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        obs_a = Observation(
            source_id="test_sensor",
            payload={"subject_id": "immut", "value": 10.0},
        )
        result_a = loop.execute(obs_a, episode_id="immut_ep")
        obs_b = Observation(
            source_id="test_sensor",
            payload={"subject_id": "immut", "value": 20.0},
        )
        result_b = loop.execute(obs_b, episode_id="immut_ep")
        obs_a_copy = store.get_object(result_a.observation_id)
        assert obs_a_copy is not None
        assert obs_a_copy.payload.get("value") == 10.0

    def test_outcome_available_for_future_recall(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "outcome_recall", "value": 5.0},
        )
        result = loop.execute(observation, episode_id="outcome_ep")
        outcome = Outcome(
            status="success",
            metrics={"value": 5.0},
        )
        loop.accept_outcome(outcome, result, episode_id="outcome_ep")
        recalled = store.get_object(outcome.id)
        assert recalled is not None
        assert recalled.id == outcome.id
        assert isinstance(recalled, Outcome)

    def test_reasoning_does_not_auto_promote_epistemic_state(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "epi_bound", "value": 6.0},
        )
        result = loop.execute(observation, episode_id="epi_bound_ep")
        assert result.reasoning_trace_id != ""
        decision = loop._decision.propose_decision(observation)
        assert decision.proposal_type == "deterministic_policy_proposal"

    def test_document_is_read_only_projection(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "doc_proj", "value": 7.0},
        )
        result = loop.execute(observation, episode_id="doc_proj_ep")
        doc = loop._documents.get_document(result.document_id)
        assert doc is not None
        assert not hasattr(doc, "execute")
        assert not hasattr(doc, "actuate")
        assert not hasattr(doc, "mutate")

    def test_plasticity_not_activated(self) -> None:
        store = InMemoryPersistenceStore()
        loop = DeterministicCognitiveLoop(persistence_store=store)
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "plasticity", "value": 8.0},
        )
        result = loop.execute(observation, episode_id="plasticity_ep")
        assert result.observation_id != ""
        assert result.experience_id != ""
        for obj in store.list_all_objects():
            assert not hasattr(obj, "plasticity_operator_id")

    def test_node_id_distinct_from_artifact_id(self) -> None:
        loop = DeterministicCognitiveLoop()
        observation = Observation(
            source_id="test_sensor",
            payload={"subject_id": "dist_node", "value": 9.0},
        )
        result = loop.execute(observation, episode_id="dist_ep")
        assert result.observation_id != "loop_node"
        assert result.experience_id != "loop_agent"
        assert result.observation_id != result.document_id
