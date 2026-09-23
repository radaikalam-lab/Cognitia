"""Tests for Representation Boundary and Security Sanitization."""

from cognitia.abi.types import Observation
from cognitia.directional.types import DirectionalSpecification
from cognitia.epistemic.types import Evidence, EvidenceDirection
from cognitia.learning.representation import RepresentationAdapter


def test_observation_adaptation_and_sanitization():
    """Verify that Observation is adapted cleanly and execution attempts are redacted."""
    obs = Observation(
        source_id="untrusted_web_sensor",
        payload={
            "metric": 42.0,
            "text": "Normal acoustic reading with import os; os.system('rm -rf /') and Bearer secret_token_12345",
        },
    )

    rep = RepresentationAdapter.adapt_observation(obs)
    assert rep.representation_version == "1.0.0"
    assert rep.features["metric"] == 42.0
    assert rep.is_trusted is False
    assert "[REDACTED_SECURITY_PAYLOAD]" in rep.sanitized_text
    assert "os.system" not in rep.sanitized_text
    assert "secret_token_12345" not in rep.sanitized_text


def test_evidence_adaptation():
    """Verify adaptation of canonical Evidence."""
    ev = Evidence(
        target_id="claim_001",
        direction=EvidenceDirection.SUPPORT,
        confidence=0.92,
        weight=1.5,
        metadata={"frequency_hz": 440.0},
    )

    rep = RepresentationAdapter.adapt_evidence(ev)
    assert rep.input_type == "evidence"
    assert rep.features["confidence"] == 0.92
    assert rep.features["frequency_hz"] == 440.0
    assert rep.is_trusted is True


def test_directional_specification_adaptation():
    """Verify adaptation of DirectionalSpecification."""
    spec = DirectionalSpecification(
        objectives=("Maximize SNR", "Preserve resonance"),
        constraints=("Max power 50W", "Latency < 10ms"),
        success_criteria=("SNR > 25dB",),
    )

    rep = RepresentationAdapter.adapt_directional_spec(spec)
    assert rep.input_type == "directional_specification"
    assert rep.features["constraint_count"] == 2
    assert "Maximize SNR" in rep.sanitized_text
