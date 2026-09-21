"""Epistemic tension and context conflict enricher.

Maps multi-directional evidence distributions across propositions and preserves
observational conflicts without premature resolution.
"""

from __future__ import annotations

from cognitia.abi.types import Observation
from cognitia.context.types import ContextConflict, EpistemicTension
from cognitia.epistemic.service import EpistemicService
from cognitia.epistemic.types import (
    EpistemicStatus,
    Evidence,
    EvidenceDirection,
)


class EpistemicTensionEnricher:
    """Computes epistemic tension maps and observational conflicts."""

    def compute_epistemic_tensions(
        self,
        epistemic_service: EpistemicService,
    ) -> tuple[EpistemicTension, ...]:
        """Identifies propositions with coexisting supporting and refuting evidence."""
        tensions: list[EpistemicTension] = []

        # Query all epistemic nodes across all possible statuses
        all_statuses = [
            EpistemicStatus.UNKNOWN,
            EpistemicStatus.OBSERVED,
            EpistemicStatus.HYPOTHESIS,
            EpistemicStatus.TESTABLE,
            EpistemicStatus.SUPPORTED,
            EpistemicStatus.REFUTED,
            EpistemicStatus.UNRESOLVED,
        ]

        seen_node_ids: set[str] = set()
        for status in all_statuses:
            nodes = epistemic_service.list_nodes_by_status(status)
            for node in nodes:
                if node.node_id in seen_node_ids:
                    continue
                seen_node_ids.add(node.node_id)

                if node.entity_type in ("claim", "hypothesis") and node.associated_evidence_ids:
                    supporting: list[str] = []
                    refuting: list[str] = []
                    neutral: list[str] = []

                    for ev_id in node.associated_evidence_ids:
                        ev_node = epistemic_service.get_node(ev_id)
                        if ev_node:
                            if isinstance(ev_node.content, Evidence):
                                if ev_node.content.direction == EvidenceDirection.SUPPORT:
                                    supporting.append(ev_id)
                                elif ev_node.content.direction == EvidenceDirection.REFUTE:
                                    refuting.append(ev_id)
                                else:
                                    neutral.append(ev_id)
                            elif ev_node.status == EpistemicStatus.SUPPORTED:
                                supporting.append(ev_id)
                            elif ev_node.status == EpistemicStatus.REFUTED:
                                refuting.append(ev_id)
                            else:
                                neutral.append(ev_id)

                    if supporting and refuting:
                        tensions.append(
                            EpistemicTension(
                                proposition_id=node.node_id,
                                supporting_evidence_ids=tuple(sorted(supporting)),
                                refuting_evidence_ids=tuple(sorted(refuting)),
                                neutral_evidence_ids=tuple(sorted(neutral)),
                            )
                        )

        tensions.sort(key=lambda t: t.proposition_id)
        return tuple(tensions)

    def compute_conflicts(
        self,
        chronological_observations: list[Observation],
    ) -> tuple[ContextConflict, ...]:
        """Identifies observational conflicts occurring at identical timestamps without silent selection."""
        conflicts: list[ContextConflict] = []
        ts_groups: dict[str, list[Observation]] = {}

        for obs in chronological_observations:
            ts_groups.setdefault(obs.created_at, []).append(obs)

        for ts in sorted(ts_groups.keys()):
            group = ts_groups[ts]
            if len(group) >= 2:
                obs_subjs = [o.metadata.get("subject_id") for o in group if o.metadata.get("subject_id")]
                if len(set(obs_subjs)) <= 1:
                    vals = [str(o.payload) for o in group]
                    if len(set(vals)) > 1:
                        conflicts.append(
                            ContextConflict(
                                object_ids=tuple(sorted(o.id for o in group)),
                                conflict_type="concurrent_value_divergence",
                                description=f"Conflicting payload values observed at identical timestamp {ts}",
                                timestamp=ts,
                            )
                        )

        return tuple(conflicts)
