"""Architectural tests verifying Provider Layer neutrality and Laya decoupling."""

import subprocess
import sys
import pytest

from cognitia.abi.types import Action, Decision, Observation
from cognitia.capabilities.base import (
    BaseCapability,
    CapabilityDescriptor,
    CapabilityType,
    DecisionCapability,
)
from cognitia.capabilities.registry import InMemoryCapabilityRegistry
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType


def test_core_does_not_import_laya():
    """Verify that Cognitia core contains zero imports or runtime references to Laya."""
    code = (
        "import sys\n"
        "import cognitia, cognitia.abi, cognitia.capabilities, cognitia.epistemic, "
        "cognitia.experience, cognitia.models, cognitia.provenance, cognitia.reasoning, "
        "cognitia.runtime, cognitia.service\n"
        "loaded = [m.lower() for m in sys.modules.keys()]\n"
        "assert not any('laya' in mod for mod in loaded), 'Laya found in core imports'"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"Subprocess import test failed: {result.stderr}"


def test_provider_identity_is_generic():
    """Verify that provider identification is purely a generic string in descriptors and registry."""
    descriptor = CapabilityDescriptor(
        capability_id="laya_acoustic_v1",
        capability_type=CapabilityType.DECISION,
        provider_name="laya",
        version="1.0.0",
        is_deterministic=False,
    )

    assert descriptor.provider_name == "laya"
    assert descriptor.capability_type == CapabilityType.DECISION
    assert descriptor.is_deterministic is False


def test_model_registry_supports_provider_identity():
    """Verify that ModelRegistry tracks provider identity generically without custom schemas."""
    registry = InMemoryModelRegistry()

    laya_model = ModelRecord(
        model_id="laya_foundation_v1",
        model_version="1.0.0",
        provider="laya",
        capability_type=CapabilityType.DECISION,
        calibration_checksum="f0e4c2f76c58916ec258f246851bea091d14d4247a2fc3e18694461b1816e13b",
        is_deterministic=False,
        status=ModelStatus.ACTIVE,
    )
    registry.register(laya_model)

    retrieved = registry.get("laya_foundation_v1", "1.0.0")
    assert retrieved is not None
    assert retrieved.provider == "laya"
    assert retrieved.is_deterministic is False


def test_capability_descriptor_is_provider_agnostic():
    """Verify that distinct providers (rules, ML, Laya) use identical CapabilityDescriptor schemas."""
    providers = ["deterministic_rules", "laya", "tiny_ml", "symbolic_prover"]

    for p in providers:
        desc = CapabilityDescriptor(
            capability_id=f"{p}_capability",
            capability_type=CapabilityType.DECISION,
            provider_name=p,
        )
        assert desc.provider_name == p
        assert desc.capability_type == CapabilityType.DECISION


def test_decision_remains_advisory():
    """Verify that any provider proposal (including from Laya) produces an advisory Decision object."""
    class MockLayaDecisionProvider:
        def __init__(self) -> None:
            self._descriptor = CapabilityDescriptor(
                capability_id="mock_laya_v1",
                capability_type=CapabilityType.DECISION,
                provider_name="laya",
                is_deterministic=False,
            )

        @property
        def descriptor(self) -> CapabilityDescriptor:
            return self._descriptor

        def propose_decision(self, observation: Observation, context: dict | None = None) -> Decision:
            return Decision(
                proposal_type="generative_hypothesis_proposal",
                proposed_action=Action(name="test_modulation", parameters={"target": "resonance"}),
                confidence=0.87,
                rationale="Laya generative inference identified candidate acoustic mode",
                provenance=ProvenanceRecord(producer_id="mock_laya_v1", is_deterministic=False),
            )

    provider = MockLayaDecisionProvider()
    obs = Observation(source_id="mic_array_0", payload={"spl_db": 94.2})
    decision = provider.propose_decision(obs)

    assert isinstance(decision, Decision)
    assert decision.proposal_type == "generative_hypothesis_proposal"
    assert not hasattr(decision, "actuate")
    assert not hasattr(decision, "execute")


def test_provider_artifacts_require_provenance():
    """Verify that provider-generated artifacts integrate with standard ProvenanceRecord."""
    prov = ProvenanceRecord(
        source_type=SourceType.NEURAL_MODEL,
        producer_id="laya_inference_node_1",
        capability_id="laya_decision_v1",
        model_id="laya_foundation_v1",
        model_version="1.0.0",
        is_deterministic=False,
    )

    assert prov.source_type == SourceType.NEURAL_MODEL
    assert prov.producer_id == "laya_inference_node_1"
    assert prov.is_deterministic is False
