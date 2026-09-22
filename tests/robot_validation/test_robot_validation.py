"""Cognitia Phase 10 Robotics Dataset Validation Tests.

Validates that Cognitia can consume externally recorded robotic observations
and produce deterministic, provenance-aware, epistemically disciplined
cognitive representations without confusing observation, inference, outcome,
or authority.

This is an integration/validation harness, not a robotics-control subsystem.
"""

from __future__ import annotations

import pytest

from cognitia.abi.types import Action, Observation, Outcome
from cognitia.integration.loop import DeterministicCognitiveLoop
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.recall.types import RecallObjectType, RecallQuery
from cognitia.documents.types import SectionType

from tests.robot_validation.adapter import RobotDatasetAdapter, RobotEpisodeRecord
from tests.robot_validation.fixtures import get_scenario


class TestRoboticsDatasetValidation:
    """Thin external validation harness for robotics dataset processing."""

    def setup_method(self) -> None:
        self.store = InMemoryPersistenceStore()
        self.loop = DeterministicCognitiveLoop(persistence_store=self.store)
        self.adapter = RobotDatasetAdapter()

    def _process_episode(self, scenario: str) -> list:
        records = get_scenario(scenario)
        results = []
        for record in records:
            observation = self.adapter.to_observation(record)
            experience = self.adapter.to_experience(observation, record.episode_id)
            result = self.loop.execute(experience.observation, episode_id=record.episode_id)
            outcome = self.adapter.to_outcome(experience.observation)
            if outcome:
                self.loop.accept_outcome(outcome, result, episode_id=record.episode_id)
            results.append((record, observation, result, outcome))
        return results

    # Scenario A — Successful episode

    def test_successful_episode_produces_experience_and_evidence(self) -> None:
        results = self._process_episode("success")
        assert len(results) == 4
        final_record, final_obs, final_result, final_outcome = results[-1]
        assert final_result.observation_id == final_obs.id
        assert final_result.experience_id != ""
        assert final_result.decision_id is not None
        assert final_result.document_id is not None
        assert final_outcome is not None
        assert final_outcome.status == "success"

    def test_successful_episode_provenance_preserved(self) -> None:
        results = self._process_episode("success")
        final_result = results[-1][2]
        assert final_result.observation_id in final_result.provenance_chain
        assert final_result.experience_id in final_result.provenance_chain

    # Scenario B — Failed episode

    def test_failed_episode_produces_failure_evidence(self) -> None:
        results = self._process_episode("failure")
        final_record, final_obs, final_result, final_outcome = results[-1]
        assert final_result.observation_id == final_obs.id
        assert final_result.experience_id != ""
        assert final_outcome is not None
        assert final_outcome.status == "failure"
        assert final_obs.payload.get("failure_reason") == "object_slipped_during_lift"

    def test_failed_episode_does_not_auto_determine_physical_cause(self) -> None:
        results = self._process_episode("failure")
        final_obs = results[-1][1]
        failure_reason = final_obs.payload.get("failure_reason", "")
        assert "grasp_force" not in failure_reason.lower()

    # Scenario C — Ambiguous / insufficient evidence

    def test_ambiguous_episode_does_not_fabricate_outcome(self) -> None:
        results = self._process_episode("ambiguous")
        final_record, final_obs, final_result, final_outcome = results[-1]
        assert final_result.observation_id == final_obs.id
        assert final_result.experience_id != ""
        assert final_outcome is None

    # Dataset mapping

    def test_robot_state_maps_to_canonical_observation(self) -> None:
        records = get_scenario("success")
        record = records[0]
        observation = self.adapter.to_observation(record)
        assert isinstance(observation, Observation)
        assert observation.source_id == record.source_node
        assert observation.payload["phase"] == record.phase
        assert observation.payload["task"] == record.task
        assert "robot_state_9d" in observation.payload
        assert "action_9d" in observation.payload

    def test_episode_identity_preserved_as_external_metadata(self) -> None:
        records = get_scenario("success")
        record = records[0]
        observation = self.adapter.to_observation(record)
        assert observation.metadata["episode_id"] == record.episode_id
        assert observation.metadata["dataset"] == "ExylosAi/pick_and_place_sample"

    # Authority boundary

    def test_dataset_action_is_not_cognitia_action(self) -> None:
        records = get_scenario("success")
        record = records[0]
        observation = self.adapter.to_observation(record)
        experience = self.adapter.to_experience(observation, record.episode_id)
        action = experience.action
        assert isinstance(action, Action)
        assert action.name == "dataset_recorded_action"
        assert action.target_node == record.source_node

    def test_no_robot_command_or_hardware_operation(self) -> None:
        results = self._process_episode("success")
        for _, observation, result, _ in results:
            assert not hasattr(result, "execute")
            assert not hasattr(result, "actuate")
            assert "command" not in str(observation.payload).lower()

    # Provenance

    def test_all_artifacts_have_dataset_provenance(self) -> None:
        results = self._process_episode("success")
        for _, observation, result, _ in results:
            assert result.observation_id in result.provenance_chain
            assert result.experience_id in result.provenance_chain

    # Contradiction preservation

    def test_contradictory_metadata_preserved(self) -> None:
        records = get_scenario("failure")
        record = records[-1]
        observation = self.adapter.to_observation(record)
        assert observation.payload.get("reported_success") is False
        assert observation.payload.get("failure_reason") is not None
        result = self.loop.execute(observation, episode_id=record.episode_id)
        assert result.observation_id in result.provenance_chain

    # Multi-cycle isolation

    def test_multiple_episodes_remain_isolated(self) -> None:
        success_results = self._process_episode("success")
        failure_results = self._process_episode("failure")
        success_ids = {r[2].observation_id for r in success_results}
        failure_ids = {r[2].observation_id for r in failure_results}
        assert success_ids.isdisjoint(failure_ids)

    # Determinism

    def test_repeated_processing_is_structurally_deterministic(self) -> None:
        store_a = InMemoryPersistenceStore()
        loop_a = DeterministicCognitiveLoop(persistence_store=store_a)
        store_b = InMemoryPersistenceStore()
        loop_b = DeterministicCognitiveLoop(persistence_store=store_b)
        records = get_scenario("success")
        for record in records:
            obs_a = self.adapter.to_observation(record)
            obs_b = self.adapter.to_observation(record)
            result_a = loop_a.execute(obs_a, episode_id=record.episode_id)
            result_b = loop_b.execute(obs_b, episode_id=record.episode_id)
            assert len(result_a.provenance_chain) == len(result_b.provenance_chain)
            assert result_a.experience_id != result_b.experience_id

    # Failure isolation

    def test_malformed_record_does_not_corrupt_store(self) -> None:
        malformed = RobotEpisodeRecord(
            episode_id="",
            frame_index=-1,
            timestamp="",
            robot_state_9d=(),
            action_9d=(),
            phase="",
            success=None,
            failure_reason=None,
            correction=None,
            derived_metrics={},
            task="",
            source="",
            source_node="",
        )
        observation = self.adapter.to_observation(malformed)
        result = self.loop.execute(observation, episode_id="malformed_ep")
        assert result.observation_id == observation.id
        assert result.experience_id != ""
        retrieved = self.store.get_object(observation.id)
        assert retrieved is not None
        assert retrieved.id == observation.id

    # Document projection

    def test_document_projection_does_not_become_authority(self) -> None:
        results = self._process_episode("success")
        final_result = results[-1][2]
        doc = self.loop._documents.get_document(final_result.document_id)
        assert doc is not None
        assert not hasattr(doc, "execute")
        assert not hasattr(doc, "actuate")

    # Recall

    def test_episodes_are_recallable(self) -> None:
        results = self._process_episode("success")
        recall_result = self.loop._recall.recall(
            RecallQuery(
                episode_id="robot_success_ep_001",
                object_types=(RecallObjectType.EXPERIENCE_RECORD,),
                limit=10,
            )
        )
        recalled_ids = [candidate.object.id for candidate in recall_result.candidates]
        assert results[-1][2].experience_id in recalled_ids
