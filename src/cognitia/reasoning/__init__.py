"""Cognitia Reasoning Module.

Defines cognitive reasoning modes, derivation steps, immutable reasoning traces,
reasoning input snapshots, candidate results, and deterministic modular strategies.
"""

from cognitia.reasoning.capability import (
    DeterministicMockReasoner,
    EngineReasoningCapability,
    ReasoningCapability,
)
from cognitia.reasoning.engine import (
    DeterministicReasoningEngine,
    ReasoningEngine,
)
from cognitia.reasoning.strategies import (
    AbductiveReasoner,
    AnalogicalReasoner,
    CausalReasoner,
    CounterfactualReasoner,
    DeductiveReasoner,
    ReasoningStrategy,
)
from cognitia.reasoning.types import (
    AbductiveHypotheses,
    AnalogicalMapping,
    CausalHypothesis,
    CounterfactualScenario,
    DeductiveConclusion,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)

__all__ = [
    # Types
    "ReasoningMode",
    "ReasoningStep",
    "ReasoningTrace",
    "ReasoningInput",
    "ReasoningResult",
    "ReasoningResidual",
    "DeductiveConclusion",
    "AbductiveHypotheses",
    "AnalogicalMapping",
    "CausalHypothesis",
    "CounterfactualScenario",
    # Capability & Engine
    "ReasoningCapability",
    "EngineReasoningCapability",
    "DeterministicMockReasoner",
    "ReasoningEngine",
    "DeterministicReasoningEngine",
    "ReasoningStrategy",
    "DeductiveReasoner",
    "AbductiveReasoner",
    "AnalogicalReasoner",
    "CausalReasoner",
    "CounterfactualReasoner",
]
