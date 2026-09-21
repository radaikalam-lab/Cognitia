"""Cognitia Reasoning Engine and Orchestrator.

Implements provider-neutral deterministic reasoning orchestration over immutable ReasoningInput snapshots.
Dispatches to modular reasoning strategies (Deduction, Abduction, Analogy, Causal, Counterfactual)
and ensures complete provenance and auditability.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from cognitia.abi.types import (
    CognitiveObject,
    Observation,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.attention.types import AttentionResult
from cognitia.context.types import CognitiveContext
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.strategies import (
    AbductiveReasoner,
    AnalogicalReasoner,
    CausalReasoner,
    CounterfactualReasoner,
    DeductiveReasoner,
    ReasoningStrategy,
)
from cognitia.reasoning.types import (
    ReasoningInput,
    ReasoningMode,
    ReasoningResult,
    ReasoningTrace,
)
from cognitia.rules.types import CognitiveRule


@runtime_checkable
class ReasoningEngine(Protocol):
    """Protocol for provider-neutral cognitive reasoning orchestration."""

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Execute reasoning over an immutable ReasoningInput snapshot."""
        ...

    def build_snapshot(
        self,
        context: CognitiveContext,
        attention_result: AttentionResult | None = None,
        mode: ReasoningMode = ReasoningMode.DEDUCTION,
        premises: Sequence[CognitiveObject] | None = None,
        rules: Sequence[CognitiveRule] | None = None,
        constraints: Mapping[str, Any] | None = None,
        hypothetical_interventions: Mapping[str, Any] | None = None,
        causal_graph: Sequence[tuple[str, str, str]] | None = None,
        analogy_source: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ReasoningInput:
        """Construct a self-contained, frozen ReasoningInput snapshot."""
        ...


class DeterministicReasoningEngine:
    """Deterministic reference implementation of ReasoningEngine.
    
    INVARIANTS:
    1. Orchestration only: delegates reasoning derivation to modular strategies.
    2. Input must be an immutable snapshot; does not perform live store lookups.
    3. Produces reproducible, provenance-linked ReasoningTrace and ReasoningResult.
    4. Preserves residuals and contradictions without forced resolution.
    """

    def __init__(
        self,
        strategies: Sequence[ReasoningStrategy] | None = None,
    ) -> None:
        self._strategies: dict[ReasoningMode, ReasoningStrategy] = {}
        if strategies:
            for s in strategies:
                self._strategies[s.mode] = s
        else:
            # Default reference strategies for all 5 canonical modes
            self.register_strategy(DeductiveReasoner())
            self.register_strategy(AbductiveReasoner())
            self.register_strategy(AnalogicalReasoner())
            self.register_strategy(CausalReasoner())
            self.register_strategy(CounterfactualReasoner())

    def register_strategy(self, strategy: ReasoningStrategy) -> None:
        """Register or override a strategy for a specific reasoning mode."""
        self._strategies[strategy.mode] = strategy

    def get_strategy(self, mode: ReasoningMode) -> ReasoningStrategy | None:
        """Get registered strategy for a reasoning mode."""
        return self._strategies.get(mode)

    def build_snapshot(
        self,
        context: CognitiveContext,
        attention_result: AttentionResult | None = None,
        mode: ReasoningMode = ReasoningMode.DEDUCTION,
        premises: Sequence[CognitiveObject] | None = None,
        rules: Sequence[CognitiveRule] | None = None,
        constraints: Mapping[str, Any] | None = None,
        hypothetical_interventions: Mapping[str, Any] | None = None,
        causal_graph: Sequence[tuple[str, str, str]] | None = None,
        analogy_source: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ReasoningInput:
        """Construct an immutable snapshot capturing premises, rules, and context items."""
        selected_ids: list[str] = []
        assembled_premises: list[CognitiveObject] = list(premises or [])

        # If attention result provided, gather focused item IDs
        att_id = None
        if attention_result:
            att_id = attention_result.id
            selected_ids.extend(attention_result.selected_item_ids)

        # If premises not explicitly provided, extract from context / attention
        if not assembled_premises:
            # Add reference observation if present
            if context.reference_observation_id:
                assembled_premises.append(
                    Observation(
                        id=context.reference_observation_id,
                        source_id=context.reference_source_id or "context_ref",
                        payload={"subject_id": context.reference_subject_id},
                    )
                )

        assembled_rules: list[CognitiveRule] = list(rules or [])

        parent_prov_ids = [context.id]
        if attention_result:
            parent_prov_ids.append(attention_result.id)
        parent_prov_ids.extend(p.id for p in assembled_premises)

        prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="deterministic_reasoning_engine",
            parent_ids=parent_prov_ids,
            is_deterministic=True,
        )

        return ReasoningInput(
            context_id=context.id,
            attention_result_id=att_id,
            selected_item_ids=selected_ids,
            reasoning_mode=mode,
            premises=assembled_premises,
            rules=assembled_rules,
            constraints=constraints,
            hypothetical_interventions=hypothetical_interventions,
            causal_graph=causal_graph or (),
            analogy_source=analogy_source,
            provenance=prov,
            metadata=metadata,
        )

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Dispatch reasoning execution to the registered strategy for the requested mode."""
        mode = reasoning_input.reasoning_mode
        strategy = self._strategies.get(mode)
        if not strategy:
            raise ValueError(f"No ReasoningStrategy registered for mode '{mode.value}'")

        return strategy.reason(reasoning_input)
