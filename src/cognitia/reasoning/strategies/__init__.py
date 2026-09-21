"""Cognitia Reasoning Strategies Package.

Exports the ReasoningStrategy protocol and deterministic implementations for all 5 canonical modes:
- DeductiveReasoner
- AbductiveReasoner
- AnalogicalReasoner
- CausalReasoner
- CounterfactualReasoner
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.reasoning.types import (
    ReasoningInput,
    ReasoningMode,
    ReasoningResult,
    ReasoningTrace,
)
from cognitia.reasoning.strategies.deductive import DeductiveReasoner
from cognitia.reasoning.strategies.abductive import AbductiveReasoner
from cognitia.reasoning.strategies.analogical import AnalogicalReasoner
from cognitia.reasoning.strategies.causal import CausalReasoner
from cognitia.reasoning.strategies.counterfactual import CounterfactualReasoner


@runtime_checkable
class ReasoningStrategy(Protocol):
    """Protocol for provider-agnostic reasoning mode strategies."""

    mode: ReasoningMode

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Execute structured reasoning over an immutable ReasoningInput snapshot."""
        ...


__all__ = [
    "ReasoningStrategy",
    "DeductiveReasoner",
    "AbductiveReasoner",
    "AnalogicalReasoner",
    "CausalReasoner",
    "CounterfactualReasoner",
]
