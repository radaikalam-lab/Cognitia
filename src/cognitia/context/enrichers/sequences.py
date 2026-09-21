"""Event sequence context enricher.

Identifies structural chronological event sequences without inferring causality.
"""

from __future__ import annotations

import datetime
from cognitia.abi.types import Observation
from cognitia.context.types import SequenceContext


def parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    """Safely parse ISO timestamp into timezone-aware datetime."""
    try:
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


class SequenceEnricher:
    """Computes observed chronological event sequences around an observation."""

    def compute_sequences(
        self,
        reference_observation: Observation,
        chronological_observations: list[Observation],
    ) -> tuple[SequenceContext, ...]:
        """Identifies chronological sequences and relative positions."""
        if len(chronological_observations) < 2:
            return ()

        ref_time = parse_iso_timestamp(reference_observation.created_at)

        seq_event_ids = tuple(o.id for o in chronological_observations)
        seq_positions = tuple(
            (o.id, idx) for idx, o in enumerate(chronological_observations, start=1)
        )
        seq_timestamps = tuple(
            (o.id, o.created_at) for o in chronological_observations
        )
        seq_deltas = tuple(
            (o.id, round((parse_iso_timestamp(o.created_at) - ref_time).total_seconds(), 6))
            for o in chronological_observations
        )

        seq = SequenceContext(
            sequence_id=f"seq_{reference_observation.id}",
            event_ids=seq_event_ids,
            relative_positions=seq_positions,
            timestamps=seq_timestamps,
            time_deltas=seq_deltas,
            provenance_id=reference_observation.provenance.id if hasattr(reference_observation, "provenance") else None,
        )
        return (seq,)
