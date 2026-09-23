"""Cross-project integration test simulating a Host Application (Thorium / AcoustiForge / PrintForge).

Proves the complete progression:
Host Observation -> Cognitia Representation -> Inference -> Outcome -> Feedback -> Learning Record -> Candidate -> Evaluation -> Promotion Proposal.
Verifies authority == NONE at every Cognitia stage and confirms Cognitia does NOT execute host-side actions.
"""

from typing import Any
import pytest
from cognitia.abi.types import Observation
from cognitia.learning.contract import OutcomeRecord
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import ModelRecord, ModelStatus


class MockHostDomainApplication:
    """Simulates a host application (e.g. AcoustiForge acoustic analyzer / Lean Thorium)."""

    def __init__(self, cognitia_service: AdaptiveLearningService) -> None:
        self.cognitia = cognitia_service
        self.physical_actuator_state = "IDLE"
        self.deployed_production_model = "laya_acoustic_v1:1.0.0"
        self.host_execution_count = 0

    def capture_acoustic_sensor_event(self, spl_db: float, freq_hz: float) -> dict[str, Any]:
        """Host generates observation and asks Cognitia for advisory prediction."""
        obs = Observation(
            source_id="acoustiforge_mic_array",
            payload={"spl_db": spl_db, "frequency_hz": freq_hz},
        )
        prediction = self.cognitia.predict_from_observation(obs, model_id="laya_acoustic_v1")
        assert prediction.authority == "NONE"
        return {"obs": obs, "pred": prediction}

    def report_measured_outcome(self, pred_id: str, obs_id: str, ground_truth_label: str) -> None:
        """Host measures actual physical outcome and provides feedback to Cognitia."""
        outcome = OutcomeRecord(
            source_id="acoustiforge_mic_array",
            target_prediction_id=pred_id,
            observation_id=obs_id,
            actual_values={"label": ground_truth_label},
            authority="NONE",
        )
        self.cognitia.record_outcome(outcome)
        self.cognitia.create_feedback_from_outcome(prediction_id=pred_id, outcome=outcome)

    def trigger_learning_cycle(self) -> dict[str, Any]:
        """Host requests candidate model exploration."""
        feedback_ids = [f.id for f in self.cognitia.list_feedback()]
        candidate, update, event = self.cognitia.learn_from_feedback(
            feedback_ids=feedback_ids,
            base_model_id="laya_acoustic_v1",
            seed=42,
        )
        assert candidate.authority == "NONE"
        assert update.authority == "NONE"

        # Proposal
        from cognitia.learning.representation import RepresentationAdapter
        eval_dataset = [
            {"representation": RepresentationAdapter.adapt_raw({"spl_db": 90.0}), "expected": "resonance"},
            {"representation": RepresentationAdapter.adapt_raw({"frequency_hz": 1200.0}), "expected": "harmonic"},
        ]
        proposal = self.cognitia.create_promotion_proposal(
            candidate_version=candidate.candidate_model_version,
            baseline_model_version="1.0.0",
            model_id="laya_acoustic_v1",
            dataset=eval_dataset,
        )
        assert proposal.authority == "NONE"
        return {"candidate": candidate, "proposal": proposal}

    def execute_domain_governance_decision(self, proposal_id: str, candidate_version: str, approve: bool) -> None:
        """Host governance board decides whether to adopt candidate in host system."""
        decision_str = "ACCEPTED" if approve else "REJECTED"
        decision_rec = self.cognitia.record_promotion_decision(
            proposal_id=proposal_id,
            decision=decision_str,
            decider_id="chief_acoustics_engineer",
            decider_authority="Domain Production Control",
        )
        assert decision_rec.cognitia_authority == "NONE"

        # Host performs activation domain-side IF approved:
        if approve:
            self.deployed_production_model = f"laya_acoustic_v1:{candidate_version}"
            self.host_execution_count += 1


def test_cross_project_host_integration():
    """Verify that Cognitia provides advisory intelligence while Host retains 100% production authority."""
    service = AdaptiveLearningService()
    base_model = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        provider="laya",
        status=ModelStatus.ACTIVE,
    )
    service.register_model(base_model)

    host = MockHostDomainApplication(service)

    # 1. Host captures observation and queries Cognitia
    event1 = host.capture_acoustic_sensor_event(spl_db=94.5, freq_hz=1500.0)
    assert event1["pred"].authority == "NONE"

    # 2. Host reports ground truth outcome
    host.report_measured_outcome(
        pred_id=event1["pred"].id,
        obs_id=event1["obs"].id,
        ground_truth_label="resonance",
    )

    # 3. Host triggers candidate learning & advisory proposal
    result = host.trigger_learning_cycle()
    candidate = result["candidate"]
    proposal = result["proposal"]

    # Verify Cognitia authority is NONE
    assert candidate.authority == "NONE"
    assert proposal.authority == "NONE"

    # Verify Cognitia did NOT touch host actuator or host deployed model
    assert host.deployed_production_model == "laya_acoustic_v1:1.0.0"
    assert host.physical_actuator_state == "IDLE"
    assert host.host_execution_count == 0

    # 4. Host governance approves proposal and deploys domain-side
    host.execute_domain_governance_decision(
        proposal_id=proposal.id,
        candidate_version=candidate.candidate_model_version,
        approve=True,
    )

    # Host updated its own state
    assert host.deployed_production_model == f"laya_acoustic_v1:{candidate.candidate_model_version}"
    assert host.host_execution_count == 1

    # But Cognitia's active model registry status remains unchanged
    active_in_cognitia = service.model_registry.get_active("laya_acoustic_v1")
    assert active_in_cognitia.model_version == "1.0.0"
