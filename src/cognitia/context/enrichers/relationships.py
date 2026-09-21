"""Entity neighbourhood and cross-source correlation enricher.

Discovers structural associations (same subject, episode, source, provenance)
and bounded cross-source correlations with explicit basis explanations without inferring causality.
"""

from __future__ import annotations

import datetime
from typing import Any
from cognitia.abi.types import Observation
from cognitia.context.types import (
    CorrelationReason,
    CrossSourceCorrelation,
    EntityRelation,
    EntityRelationType,
)
from cognitia.experience.record import ExperienceRecord


def parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    """Safely parse ISO timestamp into timezone-aware datetime."""
    try:
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


class RelationshipEnricher:
    """Computes deterministic structural entity relations and cross-source correlations."""

    def compute_entity_neighbourhood(
        self,
        reference_observation: Observation,
        all_observations: list[Observation],
        related_experiences: list[ExperienceRecord],
        subject_id: str | None,
        episode_id: str | None,
        source_app: str | None,
    ) -> tuple[EntityRelation, ...]:
        """Discovers structural co-occurrences and relationships."""
        relations: list[EntityRelation] = []

        for obs in all_observations:
            if obs.id == reference_observation.id:
                continue

            obs_sub = obs.metadata.get("subject_id") or (
                obs.payload.get("subject_id") if isinstance(obs.payload, dict) else None
            )
            if subject_id and obs_sub == subject_id:
                relations.append(
                    EntityRelation(
                        entity_id=reference_observation.id,
                        target_id=obs.id,
                        relation_type=EntityRelationType.SAME_SUBJECT,
                        metadata=(("subject_id", subject_id),),
                    )
                )

            obs_ep = obs.metadata.get("episode_id") or (
                obs.payload.get("episode_id") if isinstance(obs.payload, dict) else None
            )
            if episode_id and obs_ep == episode_id:
                relations.append(
                    EntityRelation(
                        entity_id=reference_observation.id,
                        target_id=obs.id,
                        relation_type=EntityRelationType.SAME_EPISODE,
                        metadata=(("episode_id", episode_id),),
                    )
                )

            obs_src = obs.metadata.get("source_application") or obs.source_id.split(":")[0]
            if source_app and obs_src == source_app:
                relations.append(
                    EntityRelation(
                        entity_id=reference_observation.id,
                        target_id=obs.id,
                        relation_type=EntityRelationType.SAME_SOURCE,
                        metadata=(("source_application", source_app),),
                    )
                )

        for exp in related_experiences:
            relations.append(
                EntityRelation(
                    entity_id=reference_observation.id,
                    target_id=exp.id,
                    relation_type=EntityRelationType.SHARED_PROVENANCE,
                )
            )

        relations.sort(key=lambda r: (r.relation_type.value, r.entity_id, r.target_id))
        return tuple(relations)

    def compute_cross_source_correlations(
        self,
        all_chronological_obs: list[Observation],
        max_correlation_window_seconds: float = 3600.0,
    ) -> tuple[CrossSourceCorrelation, ...]:
        """Discovers bounded cross-source correlations with explicit basis."""
        correlations: list[CrossSourceCorrelation] = []
        n = len(all_chronological_obs)

        for i in range(n):
            for j in range(i + 1, n):
                o_a = all_chronological_obs[i]
                o_b = all_chronological_obs[j]

                app_a = o_a.metadata.get("source_application") or o_a.source_id.split(":")[0]
                app_b = o_b.metadata.get("source_application") or o_b.source_id.split(":")[0]

                if app_a != app_b:
                    t_a = parse_iso_timestamp(o_a.created_at)
                    t_b = parse_iso_timestamp(o_b.created_at)
                    delta = round(abs((t_b - t_a).total_seconds()), 6)

                    if delta <= max_correlation_window_seconds:
                        reason = CorrelationReason.TEMPORAL_PROXIMITY
                        sub_a = o_a.metadata.get("subject_id")
                        sub_b = o_b.metadata.get("subject_id")
                        if sub_a and sub_b and sub_a == sub_b:
                            reason = CorrelationReason.SHARED_SUBJECT
                        elif o_a.metadata.get("episode_id") and o_a.metadata.get("episode_id") == o_b.metadata.get("episode_id"):
                            reason = CorrelationReason.SHARED_EPISODE

                        correlations.append(
                            CrossSourceCorrelation(
                                source_a_id=o_a.id,
                                source_b_id=o_b.id,
                                source_a_app=app_a,
                                source_b_app=app_b,
                                correlation_reason=reason,
                                time_delta_seconds=delta,
                            )
                        )

        correlations.sort(key=lambda c: (c.time_delta_seconds, c.source_a_id, c.source_b_id))
        return tuple(correlations)
