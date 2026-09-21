"""Cognitia Cognitive Context Module.

Exports schemas, context assembler SPI, deterministic reference implementation,
and Phase 3A Context Enrichment structures.
"""

from __future__ import annotations

from cognitia.context.engine import (
    ContextAssembler,
    DeterministicContextAssembler,
)
from cognitia.context.types import (
    AggregateContext,
    CognitiveContext,
    ContextCompression,
    ContextConflict,
    ContextDeviation,
    ContextItem,
    ContextQuery,
    CorrelationReason,
    CrossSourceCorrelation,
    DeviationType,
    EntityRelation,
    EntityRelationType,
    EpistemicTension,
    ProvenanceNeighbourhood,
    RecurrenceContext,
    RelevanceReason,
    SequenceContext,
    StateReconstruction,
    StateVariable,
    TemporalContext,
    TemporalRelation,
    TemporalRelationType,
)

__all__ = [
    "AggregateContext",
    "CognitiveContext",
    "ContextAssembler",
    "ContextCompression",
    "ContextConflict",
    "ContextDeviation",
    "ContextItem",
    "ContextQuery",
    "CorrelationReason",
    "CrossSourceCorrelation",
    "DeterministicContextAssembler",
    "DeviationType",
    "EntityRelation",
    "EntityRelationType",
    "EpistemicTension",
    "ProvenanceNeighbourhood",
    "RecurrenceContext",
    "RelevanceReason",
    "SequenceContext",
    "StateReconstruction",
    "StateVariable",
    "TemporalContext",
    "TemporalRelation",
    "TemporalRelationType",
]
