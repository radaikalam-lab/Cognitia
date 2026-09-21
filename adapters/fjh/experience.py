"""Flash Joule Heating (FJH) Experience Formation.

Constructs domain-neutral Cognitia ExperienceRecords from sequences
of related FJH observations across experiment lifecycles.
"""

from __future__ import annotations

import enum
from typing import Any

from cognitia.abi.types import Observation
from cognitia.experience.record import ExperienceBuilder, ExperienceRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType


class FJHLifecycleType(str, enum.Enum):
    """Standard Flash Joule Heating experiment workflows."""

    SINGLE_SHOT = "FJHSingleShot"
    PARAMETER_SWEEP = "FJHParameterSweep"
    PRECURSOR_COMPARISON = "FJHPrecursorComparison"
    SCALE_UP = "FJHScaleUp"
    REPRODUCIBILITY_CHECK = "FJHReproducibilityCheck"


class FJHExperienceBuilder:
    """Utility for aggregating related FJH observations into a structured ExperienceRecord."""

    @staticmethod
    def build_lifecycle_experience(
        lifecycle_id: str,
        lifecycle_type: str | FJHLifecycleType,
        observations: list[Observation],
        environment_id: str = "fjh_lab",
        agent_id: str = "fjh_operator",
        additional_context: dict[str, Any] | None = None,
    ) -> ExperienceRecord:
        """Construct a lineage-preserving ExperienceRecord from a series of FJH observations."""
        type_str = (
            lifecycle_type.value
            if isinstance(lifecycle_type, FJHLifecycleType)
            else str(lifecycle_type)
        )

        builder = (
            ExperienceBuilder(
                source_application="fjh",
                episode_id=lifecycle_id,
            )
            .with_environment(environment_id)
            .with_agent(agent_id)
        )

        if observations:
            builder.with_observation(observations[0])

        # Extract experiment and precursor identifiers if present
        experiment_ids: set[str] = set()
        precursor_ids: set[str] = set()
        chamber_ids: set[str] = set()
        for obs in observations:
            meta = obs.metadata
            exp_id = meta.get("experiment_id") or obs.payload.get("experiment_id")
            prec_id = meta.get("precursor_id") or obs.payload.get("precursor_id")
            ch_id = meta.get("chamber_id") or obs.payload.get("chamber_id")
            if exp_id:
                experiment_ids.add(str(exp_id))
            if prec_id:
                precursor_ids.add(str(prec_id))
            if ch_id:
                chamber_ids.add(str(ch_id))

        builder.with_metadata("source_application", "fjh")
        builder.with_metadata("lifecycle_type", type_str)
        builder.with_metadata("lifecycle_id", lifecycle_id)
        builder.with_metadata("observation_count", len(observations))
        builder.with_metadata("observation_ids", [obs.id for obs in observations])

        if experiment_ids:
            builder.with_metadata("experiment_ids", sorted(list(experiment_ids)))
        if precursor_ids:
            builder.with_metadata("precursor_ids", sorted(list(precursor_ids)))
        if chamber_ids:
            builder.with_metadata("chamber_ids", sorted(list(chamber_ids)))
        if additional_context:
            for k, v in additional_context.items():
                builder.with_metadata(k, v)

        # Build composite provenance linking to all source observations
        prov = ProvenanceRecord(
            source_type=SourceType.SENSOR,
            producer_id="fjh_adapter:experience_builder",
            parent_ids=[obs.id for obs in observations],
            is_deterministic=True,
        )
        builder.with_provenance(prov)

        return builder.build()
