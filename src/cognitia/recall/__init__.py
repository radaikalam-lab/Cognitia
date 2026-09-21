"""Cognitia Cognitive Recall Module.

Provides deterministic, offline, read-only cognitive recall over historical
experience and cognitive objects. Recall is provider-independent, snapshot-safe,
and explicitly NOT equivalent to attention, reasoning, learning, truth, or causality.
"""

from cognitia.recall.engine import InMemoryRecallEngine, RecallEngine
from cognitia.recall.scoring import DeterministicRecallScoring
from cognitia.recall.trace import build_recall_trace
from cognitia.recall.types import (
    RecallCandidate,
    RecallObjectType,
    RecallQuery,
    RecallResult,
    RecallScore,
    RecallTrace,
    ScoreComponent,
    ScoreComponentType,
)

__all__ = [
    "InMemoryRecallEngine",
    "RecallEngine",
    "DeterministicRecallScoring",
    "RecallCandidate",
    "RecallObjectType",
    "RecallQuery",
    "RecallResult",
    "RecallScore",
    "RecallTrace",
    "ScoreComponent",
    "ScoreComponentType",
    "build_recall_trace",
]
