"""Tests for LocalCognitiveRuntime assembly, custom configuration, and execution."""

import pytest

from cognitia.abi.types import Observation
from cognitia.capabilities.base import (
    CapabilityDescriptor,
    CapabilityType,
    DecisionCapability,
)
from cognitia.capabilities.registry import InMemoryCapabilityRegistry
from cognitia.reasoning.types import ReasoningMode
from cognitia.runtime.local import LocalCognitiveRuntime


def test_runtime_custom_injection():
    """Verify runtime properly takes injected custom services."""
    custom_caps = InMemoryCapabilityRegistry()
    runtime = LocalCognitiveRuntime(capability_registry=custom_caps)

    # Empty custom registry should bootstrap default deterministic capabilities
    assert len(runtime.capabilities.list_all()) >= 2


def test_runtime_unsupported_reasoning_mode_error():
    """Verify clean error when no registered provider supports a given mode."""
    # Create empty registry without default providers
    custom_caps = InMemoryCapabilityRegistry()

    class OnlyDeductionCapability:
        def __init__(self) -> None:
            self._descriptor = CapabilityDescriptor(
                capability_id="deduction_only",
                capability_type=CapabilityType.REASONING,
                provider_name="test",
            )
            self.supported_modes = {ReasoningMode.DEDUCTION}
            self.capability_id = "deduction_only"
            self.provider_name = "test"
            self.version = "1.0.0"
            self.is_deterministic = True

        @property
        def descriptor(self) -> CapabilityDescriptor:
            return self._descriptor

        def reason(self, mode, premises, context=None):
            pass

    custom_caps.register(OnlyDeductionCapability())
    runtime = LocalCognitiveRuntime(capability_registry=custom_caps)

    with pytest.raises(RuntimeError, match="No ReasoningCapability registered for mode analogy"):
        runtime.request_reasoning(ReasoningMode.ANALOGY, premises=[])
