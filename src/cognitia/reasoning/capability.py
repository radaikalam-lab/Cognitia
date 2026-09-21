"""Cognitia Reasoning Capability Protocol and Reference Implementation."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import CognitiveObject
from cognitia.capabilities.base import (
    BaseCapability,
    CapabilityDescriptor,
    CapabilityType,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.engine import DeterministicReasoningEngine, ReasoningEngine
from cognitia.reasoning.types import (
    ReasoningInput,
    ReasoningMode,
    ReasoningStep,
    ReasoningTrace,
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


class EngineReasoningCapability:
    """Reasoning capability adapter backed by DeterministicReasoningEngine."""

    def __init__(
        self,
        engine: ReasoningEngine | None = None,
        capability_id: str = "deterministic_reasoner_v1",
        provider_name: str = "cognitia_deterministic_reasoning_engine",
        version: str = "1.0.0",
    ) -> None:
        self._engine = engine or DeterministicReasoningEngine()
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

    @property
    def engine(self) -> ReasoningEngine:
        return self._engine

    def reason(
        self,
        mode: ReasoningMode,
        premises: list[CognitiveObject],
        context: dict[str, Any] | None = None,
    ) -> ReasoningTrace:
        if mode not in self.supported_modes:
            raise ValueError(f"Reasoning mode {mode} not supported by {self.capability_id}")

        ctx_dict = context or {}
        input_snapshot = ReasoningInput(
            context_id=ctx_dict.get("context_id", ""),
            attention_result_id=ctx_dict.get("attention_result_id"),
            selected_item_ids=ctx_dict.get("selected_item_ids", ()),
            reasoning_mode=mode,
            premises=premises,
            rules=ctx_dict.get("rules", ()),
            constraints=ctx_dict.get("constraints"),
            hypothetical_interventions=ctx_dict.get("hypothetical_interventions"),
            causal_graph=ctx_dict.get("causal_graph", ()),
            analogy_source=ctx_dict.get("analogy_source"),
            metadata=ctx_dict.get("metadata"),
        )
        trace, _ = self._engine.reason(input_snapshot)
        return trace


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
