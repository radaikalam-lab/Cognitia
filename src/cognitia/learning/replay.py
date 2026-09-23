"""Deterministic Learning History Replay Engine.

Reconstructs learning events, candidate model updates, parameter fingerprints,
and evaluation results from historical audit journals.
Distinguishes deterministically reproducible histories from histories where required
provenance/configuration is unavailable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import CognitiveObject, current_utc_timestamp
from cognitia.learning.contract import (
    AdaptiveLearningProvider,
    FeedbackRecord,
    LearningEvent,
    LearningUpdate,
    ModelCandidate,
    ModelEvaluation,
    OutcomeRecord,
)
from cognitia.models.registry import ModelRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType


@dataclass(frozen=True)
class ReplayVerificationResult(CognitiveObject):
    """Result of replaying historical learning and comparing against original records.

    Authority is strictly NONE.
    """

    candidate_model_id: str = ""
    candidate_model_version: str = ""
    is_replayable: bool = True
    is_exact_match: bool = True
    original_fingerprint: str = ""
    replayed_fingerprint: str = ""
    parameter_parity: bool = True
    status: str = "VERIFIED"  # "VERIFIED", "DISCREPANCY", "NON_REPLAYABLE"
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    authority: str = "NONE"
    timestamp: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id="learning_replay_engine",
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("ReplayVerificationResult authority must strictly be 'NONE'")


class LearningReplayEngine:
    """Replays historical learning events to verify deterministic reproducibility."""

    @classmethod
    def replay_candidate_learning(
        cls,
        provider: AdaptiveLearningProvider,
        base_model: ModelRecord | None,
        candidate: ModelCandidate | None,
        learning_events: list[LearningEvent],
        seed: int = 42,
        config: dict[str, Any] | None = None,
    ) -> ReplayVerificationResult:
        """Replay candidate creation from base model and learning events."""
        if not candidate or not base_model:
            return ReplayVerificationResult(
                candidate_model_id=candidate.candidate_model_id if candidate else "unknown",
                candidate_model_version=candidate.candidate_model_version if candidate else "unknown",
                is_replayable=False,
                is_exact_match=False,
                status="NON_REPLAYABLE",
                reason="Missing base_model or original candidate record in historical provenance",
                authority="NONE",
            )

        if not learning_events:
            return ReplayVerificationResult(
                candidate_model_id=candidate.candidate_model_id,
                candidate_model_version=candidate.candidate_model_version,
                is_replayable=False,
                is_exact_match=False,
                status="NON_REPLAYABLE",
                reason="No learning events provided for replay",
                authority="NONE",
            )

        if not provider.is_deterministic:
            return ReplayVerificationResult(
                candidate_model_id=candidate.candidate_model_id,
                candidate_model_version=candidate.candidate_model_version,
                is_replayable=False,
                is_exact_match=False,
                status="NON_REPLAYABLE",
                reason=f"Provider '{provider.provider_id}' is not deterministic; exact replay impossible",
                authority="NONE",
            )

        try:
            # Reconstruct candidate using the exact historical parameters
            replayed_cand, replayed_update = provider.learn(
                events=learning_events,
                base_model=base_model,
                seed=seed,
                config=config,
            )

            exact_match = (
                replayed_cand.parameter_fingerprint == candidate.parameter_fingerprint
                and replayed_cand.parameters.get("bias") == candidate.parameters.get("bias")
            )

            status = "VERIFIED" if exact_match else "DISCREPANCY"
            reason = (
                "Deterministic parameter fingerprint and weights matched exactly."
                if exact_match
                else "Parameter fingerprint or bias mismatch between original and replayed candidate."
            )

            return ReplayVerificationResult(
                candidate_model_id=candidate.candidate_model_id,
                candidate_model_version=candidate.candidate_model_version,
                is_replayable=True,
                is_exact_match=exact_match,
                original_fingerprint=candidate.parameter_fingerprint,
                replayed_fingerprint=replayed_cand.parameter_fingerprint,
                parameter_parity=exact_match,
                status=status,
                reason=reason,
                details={
                    "original_bias": candidate.parameters.get("bias"),
                    "replayed_bias": replayed_cand.parameters.get("bias"),
                    "seed": seed,
                },
                authority="NONE",
            )
        except Exception as exc:
            return ReplayVerificationResult(
                candidate_model_id=candidate.candidate_model_id,
                candidate_model_version=candidate.candidate_model_version,
                is_replayable=False,
                is_exact_match=False,
                status="ERROR",
                reason=f"Replay execution failed: {str(exc)}",
                authority="NONE",
            )
