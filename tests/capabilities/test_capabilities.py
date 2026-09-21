"""Tests for provider-agnostic Capability SPI and Registry."""

from cognitia.abi.types import Decision, Observation
from cognitia.capabilities.base import (
    CapabilityDescriptor,
    CapabilityType,
    DecisionCapability,
    DeterministicMockDecisionProvider,
)
from cognitia.capabilities.registry import InMemoryCapabilityRegistry


class CustomDeterministicRuleProvider:
    """Alternative provider implementing DecisionCapability."""

    def __init__(self) -> None:
        self._descriptor = CapabilityDescriptor(
            capability_id="custom_rule_v2",
            capability_type=CapabilityType.DECISION,
            provider_name="custom_rules",
            version="2.0.0",
            is_deterministic=True,
        )

    @property
    def descriptor(self) -> CapabilityDescriptor:
        return self._descriptor

    def propose_decision(
        self, observation: Observation, context: dict | None = None
    ) -> Decision:
        return Decision(
            proposal_type="custom_rule_proposal",
            confidence=0.99,
            rationale="Executed custom deterministic rule",
        )


def test_capability_registration_and_substitution():
    """Verify swappable capability providers through SPI."""
    registry = InMemoryCapabilityRegistry()
    mock_provider = DeterministicMockDecisionProvider()
    custom_provider = CustomDeterministicRuleProvider()

    registry.register(mock_provider)
    registry.register(custom_provider)

    assert len(registry.list_by_type(CapabilityType.DECISION)) == 2

    # Query by ID
    p1 = registry.get("mock_decision_provider_v1")
    p2 = registry.get("custom_rule_v2")

    assert p1 is not None and isinstance(p1, DecisionCapability)
    assert p2 is not None and isinstance(p2, DecisionCapability)

    obs = Observation(source_id="test_sensor")
    d1 = p1.propose_decision(obs)
    d2 = p2.propose_decision(obs)

    assert d1.proposal_type == "deterministic_policy_proposal"
    assert d2.proposal_type == "custom_rule_proposal"
