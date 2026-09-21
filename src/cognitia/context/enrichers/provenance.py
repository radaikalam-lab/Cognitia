"""Provenance neighbourhood enricher.

Exposes bounded upstream and downstream lineage relationships using the canonical Provenance DAG.
"""

from __future__ import annotations

from cognitia.abi.types import Observation
from cognitia.context.types import ProvenanceNeighbourhood


class ProvenanceNeighbourhoodEnricher:
    """Traverses and constructs bounded provenance neighbourhoods."""

    def compute_provenance_neighbourhood(
        self,
        reference_observation: Observation,
        source_app: str | None,
        related_experience_ids: tuple[str, ...],
        active_rule_ids: tuple[str, ...],
        max_depth: int = 5,
    ) -> tuple[ProvenanceNeighbourhood, ...]:
        """Builds bounded provenance lineage connections."""
        derived_from: list[str] = []
        produced_by: list[str] = [source_app] if source_app else []
        measured_by: list[str] = [reference_observation.source_id]

        # Extract from metadata if present
        if "parent_ids" in reference_observation.metadata:
            parents = reference_observation.metadata["parent_ids"]
            if isinstance(parents, (list, tuple)):
                derived_from.extend(parents[:max_depth])
        if "producer_id" in reference_observation.metadata:
            produced_by.append(reference_observation.metadata["producer_id"])

        if hasattr(reference_observation, "provenance") and reference_observation.provenance:
            prov = reference_observation.provenance
            derived_from.extend(prov.parent_ids[:max_depth])
            if prov.producer_id:
                produced_by.append(prov.producer_id)
            if prov.model_id:
                produced_by.append(prov.model_id)

        prov_neighbourhood = ProvenanceNeighbourhood(
            root_entity_id=reference_observation.id,
            derived_from_ids=tuple(sorted(set(derived_from))),
            produced_by_ids=tuple(sorted(set(produced_by))),
            measured_by_ids=tuple(sorted(set(measured_by))),
            referenced_by_ids=tuple(sorted(set(related_experience_ids + active_rule_ids))),
        )
        return (prov_neighbourhood,)
