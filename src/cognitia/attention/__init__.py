"""Cognitia Cognitive Attention Package.

Provides domain-neutral, task-dependent prioritization and focus capabilities over CognitiveContext.
"""

from cognitia.attention.engine import (
    AttentionEngine,
    DeterministicAttentionEngine,
)
from cognitia.attention.types import (
    AttentionItem,
    AttentionQuery,
    AttentionReason,
    AttentionResult,
)

__all__ = [
    "AttentionEngine",
    "AttentionItem",
    "AttentionQuery",
    "AttentionReason",
    "AttentionResult",
    "DeterministicAttentionEngine",
]
