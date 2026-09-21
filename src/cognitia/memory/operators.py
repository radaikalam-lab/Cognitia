"""Cognitia Plasticity Operators.

Implements deterministic, read-only plasticity operators that examine
historical cognitive experience and propose candidate learning artifacts.

Operators MUST NOT mutate persistence, memory, models, rules, epistemic state,
or any production cognitive structures. Candidate generation is strictly
a proposal operation.
"""

from __future__ import annotations

from cognitia.memory.consolidation import PlasticityOperator
from cognitia.memory.types import (
    CandidateLearningArtifact,
    CandidateType,
    MemoryContext,
    OperatorLifecycleStatus,
    OperatorRecord,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class DeterministicPatternOperator:
    """Deterministic pattern discovery operator.

    Identifies explicit recurring structures in historical experience:
    - same event type
    - same subject
    - same explicit state
    - same metric
    - same operating condition
    - repeated sequence
    - repeated interval
    - repeated outcome

    MUST NOT infer causality, intent, meaning, or truth.
    """

    def __init__(
        self,
        operator_id: str = "deterministic_pattern_operator",
        operator_version: str = "1.0.0",
    ) -> None:
        self.operator_id = operator_id
        self.operator_version = operator_version
        self.operator_type = "pattern_discovery"

    def propose(self, context: MemoryContext) -> CandidateLearningArtifact:
        experiences = list(context.experiences)
        if not experiences:
            return CandidateLearningArtifact(
                candidate_type=CandidateType.PATTERN,
                source_memory_ids=[context.id],
                proposed_change={"pattern": "no_experiences", "recurrence_count": 0},
                rationale="No experiences available for pattern discovery",
                confidence=0.0,
                provider=self.operator_id,
                model_version=self.operator_version,
                provenance=ProvenanceRecord(
                    source_type=SourceType.DETERMINISTIC_RULE,
                    producer_id=f"{self.operator_id}:{self.operator_version}",
                    parent_ids=[context.id],
                    is_deterministic=True,
                ),
            )

        pattern_groups: dict[str, list[str]] = {}
        for exp in experiences:
            obs = exp.observation
            event_type = (obs.payload or {}).get("object_type") or "unknown_event"
            subject_id = (obs.payload or {}).get("subject_id") or "unknown_subject"
            key = f"{event_type}:{subject_id}"
            pattern_groups.setdefault(key, []).append(exp.id)

        recurring_patterns = {k: v for k, v in pattern_groups.items() if len(v) >= 2}

        if not recurring_patterns:
            return CandidateLearningArtifact(
                candidate_type=CandidateType.PATTERN,
                source_memory_ids=[e.id for e in experiences],
                proposed_change={"pattern": "no_recurring_pattern", "recurrence_count": 0},
                rationale="No recurring patterns detected across experiences",
                confidence=0.0,
                provider=self.operator_id,
                model_version=self.operator_version,
                provenance=ProvenanceRecord(
                    source_type=SourceType.DETERMINISTIC_RULE,
                    producer_id=f"{self.operator_id}:{self.operator_version}",
                    parent_ids=[context.id],
                    is_deterministic=True,
                ),
            )

        top_pattern_key = max(recurring_patterns, key=lambda k: len(recurring_patterns[k]))
        top_experience_ids = recurring_patterns[top_pattern_key]
        event_type, subject_id = top_pattern_key.split(":", 1)

        proposed_change = {
            "pattern_key": top_pattern_key,
            "event_type": event_type,
            "subject_id": subject_id,
            "recurrence_count": len(top_experience_ids),
            "recurring_experience_ids": top_experience_ids,
            "pattern_type": "recurring_event_subject_pair",
        }

        rationale = (
            f"Recurring pattern detected: event_type='{event_type}' "
            f"with subject_id='{subject_id}' observed {len(top_experience_ids)} times "
            f"across memory context {context.id}. "
            f"This is a descriptive observation, not a causal claim."
        )

        confidence = min(1.0, len(top_experience_ids) / max(1, len(experiences)))

        prov = ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id=f"{self.operator_id}:{self.operator_version}",
            parent_ids=[context.id] + top_experience_ids,
            is_deterministic=True,
        )

        return CandidateLearningArtifact(
            candidate_type=CandidateType.PATTERN,
            source_memory_ids=[e.id for e in experiences],
            proposed_change=proposed_change,
            rationale=rationale,
            confidence=confidence,
            provider=self.operator_id,
            model_version=self.operator_version,
            provenance=prov,
        )


class DeterministicAssociationOperator:
    """Deterministic association discovery operator.

    Detects repeated co-occurrence of distinct event types within episodes.
    Explicitly represents ASSOCIATION, never CAUSATION.

    Example:
        BoostHigh co-occurs with HighLoad
        does NOT become BoostHigh causes HighLoad.
    """

    def __init__(
        self,
        operator_id: str = "deterministic_association_operator",
        operator_version: str = "1.0.0",
    ) -> None:
        self.operator_id = operator_id
        self.operator_version = operator_version
        self.operator_type = "association_discovery"

    def propose(self, context: MemoryContext) -> CandidateLearningArtifact:
        experiences = list(context.experiences)
        if not experiences:
            return CandidateLearningArtifact(
                candidate_type=CandidateType.ASSOCIATION,
                source_memory_ids=[context.id],
                proposed_change={"association": "no_experiences", "cooccurrence_count": 0},
                rationale="No experiences available for association discovery",
                confidence=0.0,
                provider=self.operator_id,
                model_version=self.operator_version,
                provenance=ProvenanceRecord(
                    source_type=SourceType.DETERMINISTIC_RULE,
                    producer_id=f"{self.operator_id}:{self.operator_version}",
                    parent_ids=[context.id],
                    is_deterministic=True,
                ),
            )

        episode_event_types: dict[str, set[str]] = {}
        for exp in experiences:
            episode_id = exp.episode_id or "unknown_episode"
            event_type = (exp.observation.payload or {}).get("object_type") or "unknown_event"
            episode_event_types.setdefault(episode_id, set()).add(event_type)

        cooccurrence_counts: dict[tuple[str, str], int] = {}
        for episode_id, event_types in episode_event_types.items():
            sorted_types = sorted(event_types)
            for i in range(len(sorted_types)):
                for j in range(i + 1, len(sorted_types)):
                    pair = (sorted_types[i], sorted_types[j])
                    cooccurrence_counts[pair] = cooccurrence_counts.get(pair, 0) + 1

        if not cooccurrence_counts:
            return CandidateLearningArtifact(
                candidate_type=CandidateType.ASSOCIATION,
                source_memory_ids=[e.id for e in experiences],
                proposed_change={"association": "no_cooccurrence", "cooccurrence_count": 0},
                rationale="No co-occurring event pairs detected across episodes",
                confidence=0.0,
                provider=self.operator_id,
                model_version=self.operator_version,
                provenance=ProvenanceRecord(
                    source_type=SourceType.DETERMINISTIC_RULE,
                    producer_id=f"{self.operator_id}:{self.operator_version}",
                    parent_ids=[context.id],
                    is_deterministic=True,
                ),
            )

        top_pair = max(cooccurrence_counts, key=lambda k: cooccurrence_counts[k])
        cooccurrence_count = cooccurrence_counts[top_pair]
        event_a, event_b = top_pair

        proposed_change = {
            "association_pair": [event_a, event_b],
            "cooccurrence_count": cooccurrence_count,
            "cooccurring_episode_count": cooccurrence_count,
            "association_type": "co_occurrence",
            "episodes": list(episode_event_types.keys()),
        }

        rationale = (
            f"Association detected: '{event_a}' co-occurs with '{event_b}' "
            f"in {cooccurrence_count} episode(s). "
            f"This describes co-occurrence only and does not imply causation."
        )

        confidence = min(1.0, cooccurrence_count / max(1, len(episode_event_types)))

        prov = ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id=f"{self.operator_id}:{self.operator_version}",
            parent_ids=[context.id],
            is_deterministic=True,
        )

        return CandidateLearningArtifact(
            candidate_type=CandidateType.ASSOCIATION,
            source_memory_ids=[e.id for e in experiences],
            proposed_change=proposed_change,
            rationale=rationale,
            confidence=confidence,
            provider=self.operator_id,
            model_version=self.operator_version,
            provenance=prov,
        )


class DeterministicRecurrenceOperator:
    """Deterministic recurrence detection operator.

    Identifies repeated temporal patterns across experiences:
    - pattern occurred N times
    - pattern appeared in M episodes
    - median interval
    - observed interval distribution

    Remains strictly descriptive. No prediction. No causal inference.
    """

    def __init__(
        self,
        operator_id: str = "deterministic_recurrence_operator",
        operator_version: str = "1.0.0",
    ) -> None:
        self.operator_id = operator_id
        self.operator_version = operator_version
        self.operator_type = "recurrence_discovery"

    def propose(self, context: MemoryContext) -> CandidateLearningArtifact:
        experiences = list(context.experiences)
        if not experiences:
            return CandidateLearningArtifact(
                candidate_type=CandidateType.PATTERN,
                source_memory_ids=[context.id],
                proposed_change={"recurrence": "no_experiences", "occurrence_count": 0},
                rationale="No experiences available for recurrence discovery",
                confidence=0.0,
                provider=self.operator_id,
                model_version=self.operator_version,
                provenance=ProvenanceRecord(
                    source_type=SourceType.DETERMINISTIC_RULE,
                    producer_id=f"{self.operator_id}:{self.operator_version}",
                    parent_ids=[context.id],
                    is_deterministic=True,
                ),
            )

        from cognitia.abi.types import Observation
        observations: list[Observation] = []
        for exp in experiences:
            observations.append(exp.observation)

        sorted_obs = sorted(
            observations,
            key=lambda o: (o.payload or {}).get("created_at", ""),
        )
        event_types = [(o.payload or {}).get("object_type") or "unknown_event" for o in sorted_obs]

        from collections import Counter
        type_counts = Counter(event_types)
        most_common_type, most_common_count = type_counts.most_common(1)[0]

        intervals: list[float] = []
        for i in range(1, len(sorted_obs)):
            from cognitia.context.enrichers.statistics import parse_iso_timestamp
            t_prev = parse_iso_timestamp((sorted_obs[i - 1].payload or {}).get("created_at", ""))
            t_curr = parse_iso_timestamp((sorted_obs[i].payload or {}).get("created_at", ""))
            delta = max(0.0, (t_curr - t_prev).total_seconds())
            intervals.append(round(delta, 6))

        median_interval = None
        if intervals:
            import statistics
            median_interval = round(float(statistics.median(intervals)), 6)

        episode_ids = list({exp.episode_id for exp in experiences if exp.episode_id})

        proposed_change = {
            "recurring_event_type": most_common_type,
            "occurrence_count": most_common_count,
            "total_observations": len(sorted_obs),
            "episode_count": len(episode_ids),
            "intervals_seconds": intervals,
            "median_interval_seconds": median_interval,
        }

        rationale = (
            f"Recurrence pattern detected: event_type='{most_common_type}' "
            f"occurred {most_common_count} times across {len(episode_ids)} episode(s) "
            f"with median interval {median_interval} seconds. "
            f"This describes observed recurrence only."
        )

        confidence = min(1.0, most_common_count / max(1, len(sorted_obs)))

        prov = ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id=f"{self.operator_id}:{self.operator_version}",
            parent_ids=[context.id],
            is_deterministic=True,
        )

        return CandidateLearningArtifact(
            candidate_type=CandidateType.PATTERN,
            source_memory_ids=[e.id for e in experiences],
            proposed_change=proposed_change,
            rationale=rationale,
            confidence=confidence,
            provider=self.operator_id,
            model_version=self.operator_version,
            provenance=prov,
        )
