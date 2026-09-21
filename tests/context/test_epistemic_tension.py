"""Tests for Epistemic Tension Enrichment.

Validates that propositions with coexisting supporting and refuting evidence
are mapped into EpistemicTension structures without premature truth estimation or winner selection.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.epistemic.types import (
    Claim,
    EpistemicStatus,
    Evidence,
    EvidenceDirection,
)
from cognitia.runtime.local import LocalCognitiveRuntime


def test_epistemic_tension_mapping() -> None:
    runtime = LocalCognitiveRuntime()

    # Create Claim C1
    claim = Claim(
        statement="MATERIAL-ALPHA is superconducting",
        status=EpistemicStatus.UNRESOLVED,
    )
    claim_node = runtime.epistemics.register_claim(claim)

    # Register supporting evidence E1
    ev_sup = Evidence(
        target_id=claim_node.node_id,
        direction=EvidenceDirection.SUPPORT,
        confidence=0.9,
    )
    runtime.epistemics.register_evidence(ev_sup)

    # Register refuting evidence E2
    ev_ref = Evidence(
        target_id=claim_node.node_id,
        direction=EvidenceDirection.REFUTE,
        confidence=0.85,
    )
    runtime.epistemics.register_evidence(ev_ref)

    # Observation
    obs = Observation(source_id="lab:monitor", payload={"claim_id": claim_node.node_id})
    runtime.persistence.save_object(obs)

    context = runtime.assemble_context(obs)

    assert len(context.epistemic_tensions) == 1
    tension = context.epistemic_tensions[0]
    assert tension.proposition_id == claim_node.node_id
    assert ev_sup.id in tension.supporting_evidence_ids
    assert ev_ref.id in tension.refuting_evidence_ids
