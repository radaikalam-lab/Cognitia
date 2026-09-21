"""Tests for Epistemic service, propositions, evidence, and non-linear transitions."""

from cognitia.abi.types import Observation, Outcome
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.epistemic.types import (
    Challenge,
    Claim,
    EpistemicStatus,
    Evidence,
    EvidenceDirection,
    Hypothesis,
    Residual,
)


def test_epistemic_observation_and_hypothesis():
    """Verify recording observations and registering testable hypotheses."""
    service = InMemoryEpistemicService()
    obs = Observation(source_id="sensor_temp", payload={"temperature": 105.2})
    obs_node = service.record_observation(obs)

    assert obs_node.status == EpistemicStatus.OBSERVED

    hypothesis = Hypothesis(
        statement="High temperature is caused by excessive friction",
        test_criteria=["Check lubrication level", "Measure motor RPM"],
    )
    hyp_node = service.register_hypothesis(hypothesis)

    assert hyp_node.status == EpistemicStatus.HYPOTHESIS
    assert hyp_node.content == hypothesis


def test_evidence_registration_and_linking():
    """Verify registering evidence supporting a hypothesis."""
    service = InMemoryEpistemicService()
    hypothesis = Hypothesis(statement="Filter saturation degrades flow rate")
    hyp_node = service.register_hypothesis(hypothesis)

    evidence_obs = Observation(payload={"flow_lpm": 2.1, "saturation_pct": 92.0})
    evidence = Evidence(
        target_id=hypothesis.id,
        observation=evidence_obs,
        direction=EvidenceDirection.SUPPORT,
        confidence=0.88,
    )
    ev_node = service.register_evidence(evidence)

    assert ev_node.status == EpistemicStatus.SUPPORTED
    updated_hyp = service.get_node(hypothesis.id)
    assert updated_hyp is not None
    assert evidence.id in updated_hyp.associated_evidence_ids


def test_challenge_and_non_linear_transitions():
    """Verify issuing a challenge and recording state transitions without linear constraints."""
    service = InMemoryEpistemicService()
    claim = Claim(statement="System is operating within nominal boundary", confidence=0.9)
    service.register_claim(claim)

    challenge = Challenge(
        target_id=claim.id,
        basis="Residual vibration exceeds safety margin by 30%",
    )
    transition = service.issue_challenge(challenge)

    assert transition.to_status == EpistemicStatus.UNRESOLVED
    assert transition.from_status == EpistemicStatus.SUPPORTED

    claim_node = service.get_node(claim.id)
    assert claim_node is not None
    assert claim_node.status == EpistemicStatus.UNRESOLVED

    # Manual transition based on investigation
    service.transition_state(
        node_id=claim.id,
        new_status=EpistemicStatus.REFUTED,
        reason="Vibration sensor confirmed faulty bearing",
    )

    history = service.get_history(claim.id)
    assert len(history) == 2
    assert history[0].to_status == EpistemicStatus.UNRESOLVED
    assert history[1].to_status == EpistemicStatus.REFUTED


def test_residual_recording():
    """Verify recording residuals between expected and actual outcomes."""
    service = InMemoryEpistemicService()
    expected = Outcome(metrics={"efficiency": 0.85})
    actual = Outcome(metrics={"efficiency": 0.62})

    residual = Residual(
        expected_outcome=expected,
        actual_outcome=actual,
        discrepancy_magnitude=0.23,
        discrepancy_details={"primary_deficit": "thermal_dissipation"},
    )
    res_node = service.record_residual(residual)

    assert res_node.status == EpistemicStatus.OBSERVED
    assert res_node.content == residual
