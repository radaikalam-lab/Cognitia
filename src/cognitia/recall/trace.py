"""Cognitia Recall Trace Utilities.

Provides helpers for constructing and inspecting RecallTrace instances.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from cognitia.recall.engine import InMemoryRecallEngine
from cognitia.recall.types import RecallQuery, RecallResult, RecallTrace


def build_recall_trace(
    result: RecallResult,
    engine: InMemoryRecallEngine,
    scoring_profile: str = "default",
    metadata: dict[str, Any] | None = None,
) -> RecallTrace:
    """Build a RecallTrace from a completed RecallResult.

    Args:
        result: completed recall result.
        engine: recall engine used for execution.
        scoring_profile: name of the scoring profile used.
        metadata: optional additional metadata.

    Returns:
        Populated RecallTrace.
    """
    started_at = result.query.created_at
    completed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return RecallTrace(
        trace_id=result.trace_id or result.query.query_id,
        query=result.query,
        engine_id=engine._engine_id,
        total_evaluated=result.total_evaluated,
        total_matched=result.total_matched,
        returned_count=len(result.candidates),
        truncated=result.truncated,
        scoring_profile=scoring_profile,
        started_at=started_at,
        completed_at=completed_at,
        metadata=dict(metadata or {}),
    )
