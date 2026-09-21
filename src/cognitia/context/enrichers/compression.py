"""Deterministic structural context compression enricher.

Computes descriptive structural summaries without task-based prioritization or filtering.
"""

from __future__ import annotations

import datetime
from cognitia.abi.types import Observation
from cognitia.context.types import ContextCompression
from cognitia.epistemic.types import EpistemicStatus


def parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    """Safely parse ISO timestamp into timezone-aware datetime."""
    try:
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


class ContextCompressionEnricher:
    """Computes deterministic high-level structural metrics over assembled context."""

    def compute_compression(
        self,
        chronological_observations: list[Observation],
        epistemic_context: tuple[tuple[str, EpistemicStatus], ...],
        sequence_count: int,
        deviation_count: int,
        conflict_count: int,
    ) -> ContextCompression:
        """Produces a deterministic structural summary of context dimensions."""
        all_subjects = set()
        all_sources = set()

        for obs in chronological_observations:
            sub = obs.metadata.get("subject_id") or (
                obs.payload.get("subject_id") if isinstance(obs.payload, dict) else None
            )
            if sub:
                all_subjects.add(sub)
            src = obs.metadata.get("source_application") or obs.source_id.split(":")[0]
            if src:
                all_sources.add(src)

        supported_c = sum(1 for _, s in epistemic_context if s == EpistemicStatus.SUPPORTED)
        unresolved_c = sum(1 for _, s in epistemic_context if s in (EpistemicStatus.UNRESOLVED, EpistemicStatus.UNKNOWN))
        refuted_c = sum(1 for _, s in epistemic_context if s == EpistemicStatus.REFUTED)

        timespan_s = 0.0
        if len(chronological_observations) >= 2:
            timespan_s = max(
                0.0,
                (
                    parse_iso_timestamp(chronological_observations[-1].created_at)
                    - parse_iso_timestamp(chronological_observations[0].created_at)
                ).total_seconds(),
            )

        return ContextCompression(
            observation_count=len(chronological_observations),
            timespan_seconds=round(timespan_s, 6),
            subject_count=len(all_subjects),
            source_count=len(all_sources),
            supported_epistemic_count=supported_c,
            unresolved_epistemic_count=unresolved_c,
            refuted_epistemic_count=refuted_c,
            sequence_count=sequence_count,
            deviation_count=deviation_count,
            conflict_count=conflict_count,
        )
