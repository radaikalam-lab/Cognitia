"""Tests verifying the Authority Boundary Contract and Invariants."""

import pytest

from cognitia.abi.types import Action, Decision, Observation
from cognitia.capabilities.base import DeterministicMockDecisionProvider
from cognitia.epistemic.types import EpistemicNode, EpistemicStatus, Hypothesis


def test_decision_is_strictly_advisory():
    """Ensure that a capability produces an advisory proposal, not actuator execution."""
    provider = DeterministicMockDecisionProvider()
    obs = Observation(source_id="test_sensor", payload={"voltage": 12.4})

    decision = provider.propose_decision(obs)

    assert isinstance(decision, Decision)
    assert decision.proposal_type == "deterministic_policy_proposal"
    assert isinstance(decision.proposed_action, Action)
    # The decision carries no actuator binding or direct hardware execution interface
    assert not hasattr(decision, "execute")
    assert not hasattr(decision, "actuate")


def test_epistemic_state_is_distinct_from_physical_truth():
    """Verify that an epistemic node models internal belief state, not physical ground truth."""
    hypothesis = Hypothesis(statement="Pressure drop indicates acoustic resonance")
    node = EpistemicNode(
        node_id=hypothesis.id,
        entity_type="hypothesis",
        status=EpistemicStatus.SUPPORTED,
        confidence=0.95,
        content=hypothesis,
    )

    # Epistemic state reflects evaluation status, distinct from physical reality
    assert node.status == EpistemicStatus.SUPPORTED
    assert node.confidence < 1.0 or node.status != EpistemicStatus.UNKNOWN
    assert node.status != "PHYSICAL_FACT"


def test_runtime_experience_does_not_mutate_model_weights():
    """Verify that recording operational experience does not mutate model calibration or registry."""
    from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus
    from cognitia.experience.record import ExperienceBuilder
    from cognitia.runtime.local import LocalCognitiveRuntime

    models = InMemoryModelRegistry()
    initial_checksum = "a1b2c3d4e5f600112233445566778899aabbccddeeff00112233445566778899"
    model_record = ModelRecord(
        model_id="acoustic_model",
        model_version="1.0.0",
        calibration_checksum=initial_checksum,
        status=ModelStatus.ACTIVE,
    )
    models.register(model_record)

    runtime = LocalCognitiveRuntime(model_registry=models)

    # Ingest runtime experiences
    for i in range(10):
        exp = (
            ExperienceBuilder("acoustiforge", f"ep_{i}")
            .with_observation(Observation(payload={"freq": 440 + i}))
            .with_action(Action(name="test_pulse"))
            .with_model_version("1.0.0")
            .build()
        )
        runtime.experience.record_experience(exp)

    # Model record and checksum must remain completely untouched
    stored_model = runtime.models.get("acoustic_model", "1.0.0")
    assert stored_model is not None
    assert stored_model.calibration_checksum == initial_checksum
    assert stored_model.status == ModelStatus.ACTIVE


def test_no_domain_packages_imported_in_cognitia():
    """Verify that cognitia modules do not import domain projects (AcoustiForge, CellForge, etc.)."""
    import sys
    import cognitia

    forbidden_domains = ["acoustiforge", "cellforge", "robotics", "farm", "swarm"]
    loaded_modules = [m.lower() for m in sys.modules.keys()]

    for forbidden in forbidden_domains:
        assert not any(forbidden in mod and "cognitia" not in mod for mod in loaded_modules), (
            f"Forbidden domain module '{forbidden}' found in loaded sys.modules"
        )

