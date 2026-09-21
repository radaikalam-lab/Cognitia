"""Flash Joule Heating (FJH) Event Translator.

Translates incoming FJH domain events into canonical Cognitia Observations
while preserving experiment identity, timestamp, stage, payload, and provenance.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Observation, current_utc_timestamp
from cognitia.provenance.record import ProvenanceRecord, SourceType

from adapters.fjh.events import FJHEvent, FJHStage


class FJHEventTranslator:
    """Translates incoming FJH domain events into canonical Cognitia Observations."""

    @staticmethod
    def translate(event: FJHEvent) -> Observation:
        """Convert an FJHEvent into an immutable Cognitia Observation with full provenance."""
        stage_str = event.stage.value if isinstance(event.stage, FJHStage) else str(event.stage)
        timestamp = event.timestamp or current_utc_timestamp()

        # Build clean observation payload preserving all original data
        obs_payload: dict[str, Any] = {
            "stage": stage_str,
            "experiment_id": event.experiment_id,
            "precursor_id": event.precursor_id,
            "chamber_id": event.chamber_id,
            "operator_id": event.operator_id,
            "data": dict(event.payload),
        }

        # Build metadata for filtering and indexing
        metadata: dict[str, Any] = {
            "source_application": "fjh",
            "stage": stage_str,
            "experiment_id": event.experiment_id,
            "precursor_id": event.precursor_id,
            "chamber_id": event.chamber_id,
            "operator_id": event.operator_id,
        }

        # Merge additional metadata
        metadata.update(event.metadata)

        source_id = f"fjh:{event.experiment_id}:{stage_str}"

        obs = Observation(
            source_id=source_id,
            payload=obs_payload,
            created_at=timestamp,
            metadata=metadata,
        )

        return obs
