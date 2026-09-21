"""Tests verifying that Memory preserves Epistemic Status and handles contradictions."""

import pytest

from cognitia.epistemic.types import Claim, EpistemicStatus, Hypothesis
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.memory.types import MemoryQuery
from cognitia.persistence.store import InMemoryPersistenceStore


def test_memory_preserves_epistemic_status_distinction():
    """Verify that MemoryContext distinguishes supported vs refuted propositions (Memory != Truth)."""
    persistence = InMemoryPersistenceStore()

    h_supported = Hypothesis(
        statement="Frequency modulation stabilizes flow",
        initial_status=EpistemicStatus.SUPPORTED,
    )
    h_refuted = Hypothesis(
        statement="Temperature increase causes cavitation",
        initial_status=EpistemicStatus.REFUTED,
    )

    persistence.save_object(h_supported)
    persistence.save_object(h_refuted)

    memory = InMemoryMemoryStore(persistence_store=persistence)
    context = memory.get_context(MemoryQuery(object_types=["hypothesis"]))

    assert len(context.hypotheses) == 2
    assert context.epistemic_states[h_supported.id] == EpistemicStatus.SUPPORTED
    assert context.epistemic_states[h_refuted.id] == EpistemicStatus.REFUTED


def test_contradictory_memories_remain_retrievable():
    """Verify that contradictory historical claims/experiences are preserved without silent filtering."""
    persistence = InMemoryPersistenceStore()

    claim_a = Claim(
        statement="Valve 1 seal is nominal",
        status=EpistemicStatus.SUPPORTED,
        confidence=0.9,
    )
    claim_b = Claim(
        statement="Valve 1 seal is degraded",
        status=EpistemicStatus.UNRESOLVED,
        confidence=0.4,
    )

    persistence.save_object(claim_a)
    persistence.save_object(claim_b)

    memory = InMemoryMemoryStore(persistence_store=persistence)
    all_claims = memory.retrieve(MemoryQuery(object_types=["claim"]))

    assert len(all_claims) == 2
    assert {c.id for c in all_claims} == {claim_a.id, claim_b.id}
