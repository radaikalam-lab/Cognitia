"""Temporal neighbourhood enricher.

Determines explicit, bounded temporal relationships (BEFORE, AFTER, CONCURRENT, WITHIN_WINDOW)
and relative time intervals without inferring causality.
"""

from __future__ import annotations

import datetime
from cognitia.abi.types import Observation
from cognitia.context.types import (
    ContextQuery,
    TemporalContext,
    TemporalRelation,
    TemporalRelationType,
)


def parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    """Safely parse ISO-8601 timestamp string into timezone-aware datetime."""
    try:
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


class TemporalNeighbourhoodEnricher:
    """Computes deterministic temporal relationships relative to reference observation."""

    def compute_temporal_context(
        self,
        reference_observation: Observation,
        persisted_observations: list[Observation],
        query: ContextQuery,
    ) -> tuple[TemporalContext, list[Observation]]:
        """Assembles temporal context and returns matching temporal observations."""
        ref_time = parse_iso_timestamp(reference_observation.created_at)

        preceding_ids: list[str] = []
        succeeding_ids: list[str] = []
        time_deltas: list[tuple[str, float]] = []
        relations: list[TemporalRelation] = []
        temporal_observations: list[Observation] = []

        for obj in persisted_observations:
            if obj.id == reference_observation.id:
                continue

            obj_time = parse_iso_timestamp(obj.created_at)
            delta_seconds = round((obj_time - ref_time).total_seconds(), 6)

            if delta_seconds < 0:
                # Preceding observation
                if query.temporal_window_seconds_before is None or abs(delta_seconds) <= query.temporal_window_seconds_before:
                    preceding_ids.append(obj.id)
                    time_deltas.append((obj.id, delta_seconds))
                    temporal_observations.append(obj)
                    relations.append(
                        TemporalRelation(
                            entity_id=obj.id,
                            relation_type=TemporalRelationType.BEFORE,
                            delta_seconds=delta_seconds,
                            timestamp=obj.created_at,
                        )
                    )
            elif delta_seconds > 0:
                # Succeeding observation
                if query.temporal_window_seconds_after is None or delta_seconds <= query.temporal_window_seconds_after:
                    succeeding_ids.append(obj.id)
                    time_deltas.append((obj.id, delta_seconds))
                    temporal_observations.append(obj)
                    relations.append(
                        TemporalRelation(
                            entity_id=obj.id,
                            relation_type=TemporalRelationType.AFTER,
                            delta_seconds=delta_seconds,
                            timestamp=obj.created_at,
                        )
                    )
            else:
                # Concurrent observation at exact same timestamp
                preceding_ids.append(obj.id)
                time_deltas.append((obj.id, 0.0))
                temporal_observations.append(obj)
                relations.append(
                    TemporalRelation(
                        entity_id=obj.id,
                        relation_type=TemporalRelationType.CONCURRENT,
                        delta_seconds=0.0,
                        timestamp=obj.created_at,
                    )
                )

        relations.sort(key=lambda r: (r.delta_seconds, r.entity_id))

        temporal_ctx = TemporalContext(
            reference_timestamp=reference_observation.created_at,
            window_seconds_before=query.temporal_window_seconds_before,
            window_seconds_after=query.temporal_window_seconds_after,
            preceding_observation_ids=tuple(sorted(preceding_ids)),
            succeeding_observation_ids=tuple(sorted(succeeding_ids)),
            time_deltas=tuple(sorted(time_deltas, key=lambda d: (d[1], d[0]))),
            relations=tuple(relations),
        )

        return temporal_ctx, temporal_observations
