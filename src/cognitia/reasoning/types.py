"""Cognitia Reasoning Types.

Defines canonical reasoning modes, derivation steps, and immutable reasoning traces.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import CognitiveObject
from cognitia.provenance.record import ProvenanceRecord, SourceType


class ReasoningMode(str, enum.Enum):
    """Canonical reasoning modes supported by Cognitia."""

    DEDUCTION = "deduction"
    ABDUCTION = "abduction"
    ANALOGY = "analogy"
    COUNTERFACTUAL = "counterfactual"
    CAUSAL = "causal"


@dataclass(frozen=True)
class ReasoningStep:
    """An individual step in a deliberate reasoning derivation."""

    step_number: int
    inference_rule: str
    input_references: list[str] = field(default_factory=list)
    intermediate_claim: str = ""
    confidence: float = 1.0


@dataclass(frozen=True)
class ReasoningTrace(CognitiveObject):
    """Immutable audit trace recording a structured reasoning derivation."""

    mode: ReasoningMode = ReasoningMode.DEDUCTION
    premises: list[CognitiveObject] = field(default_factory=list)
    steps: list[ReasoningStep] = field(default_factory=list)
    conclusion: CognitiveObject = field(default_factory=CognitiveObject)
    confidence: float = 1.0
    provider: str = "deterministic_reasoner"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.REASONING_ENGINE)
    )
