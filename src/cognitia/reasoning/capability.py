"""Cognitia Reasoning Capability Protocol and Reference Implementation."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import CognitiveObject
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import (
    ReasoningMode,
    ReasoningStep,
    ReasoningTrace,
)


from cognitia.capabilities.base import (
    BaseCapability,
    CapabilityDescriptor,
    CapabilityType,
)


@runtime_checkable
class ReasoningCapability(BaseCapability, Protocol):
    """Protocol for provider-agnostic reasoning capabilities."""

    @property
    def supported_modes(self) -> set[ReasoningMode]: ...

    def reason(
        self,
        mode: ReasoningMode,
        premises: list[CognitiveObject],
        context: dict[str, Any] | None = None,
    ) -> ReasoningTrace: ...


class DeterministicMockReasoner:
    """A deterministic, in-memory reference implementation of ReasoningCapability."""

    def __init__(
        self,
        capability_id: str = "mock_reasoner_v1",
        provider_name: str = "deterministic_rules",
        version: str = "1.0.0",
    ) -> None:
        self._descriptor = CapabilityDescriptor(
            capability_id=capability_id,
            capability_type=CapabilityType.REASONING,
            provider_name=provider_name,
            version=version,
            is_deterministic=True,
        )
        self.supported_modes = {
            ReasoningMode.DEDUCTION,
            ReasoningMode.ABDUCTION,
            ReasoningMode.ANALOGY,
            ReasoningMode.COUNTERFACTUAL,
            ReasoningMode.CAUSAL,
        }

    @property
    def descriptor(self) -> CapabilityDescriptor:
        return self._descriptor

    @property
    def capability_id(self) -> str:
        return self._descriptor.capability_id

    @property
    def provider_name(self) -> str:
        return self._descriptor.provider_name

    @property
    def version(self) -> str:
        return self._descriptor.version

    @property
    def is_deterministic(self) -> bool:
        return self._descriptor.is_deterministic

    def reason(
        self,
        mode: ReasoningMode,
        premises: list[CognitiveObject],
        context: dict[str, Any] | None = None,
    ) -> ReasoningTrace:
        if mode not in self.supported_modes:
            raise ValueError(f"Reasoning mode {mode} not supported by {self.capability_id}")

        premise_ids = [p.id for p in premises]
        steps = [
            ReasoningStep(
                step_number=1,
                inference_rule="identity_axiom",
                input_references=premise_ids,
                intermediate_claim=f"Evaluated {len(premises)} premises under mode {mode.value}",
                confidence=1.0,
            ),
            ReasoningStep(
                step_number=2,
                inference_rule="deterministic_synthesis",
                input_references=["step_1"],
                intermediate_claim=f"Derived conclusion for mode {mode.value}",
                confidence=1.0,
            ),
        ]

        conclusion = CognitiveObject(
            metadata={
                "reasoning_mode": mode.value,
                "premise_count": len(premises),
                "status": "derived",
            }
        )

        prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id=f"{self.provider_name}:{self.capability_id}",
            parent_ids=premise_ids,
            is_deterministic=self.is_deterministic,
        )

        return ReasoningTrace(
            mode=mode,
            premises=premises,
            steps=steps,
            conclusion=conclusion,
            confidence=1.0,
            provider=self.provider_name,
            provenance=prov,
        )
