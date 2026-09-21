"""Cognitia Cognitive Rules Module.

Exports schemas, store SPI, in-memory reference implementation,
and capability providers for human-governed cognitive rules.
"""

from __future__ import annotations

from cognitia.rules.capability import RuleEvaluationCapability, evaluate_predicate
from cognitia.rules.store import InMemoryRuleStore, RuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus

__all__ = [
    "CognitiveRule",
    "RuleStatus",
    "RuleStore",
    "InMemoryRuleStore",
    "RuleEvaluationCapability",
    "evaluate_predicate",
]
