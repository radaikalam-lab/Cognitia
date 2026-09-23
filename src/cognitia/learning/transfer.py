"""Learning Transfer Engine for Cross-Domain Adaptive Knowledge Sharing.

Implements explicit, typed, provenance-bearing, and advisory cross-domain knowledge
transfer evaluation and candidate instantiation with ZERO production authority.

Core Invariants:
1. No implicit transfer: All cross-domain knowledge movement requires an explicit proposal.
2. Authority is strictly NONE on all transfer proposals and compatibility results.
3. Target active model immutability: Transferred knowledge instantiates a target ModelCandidate
   with status=CANDIDATE; it NEVER modifies or replaces the target domain's active model.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from cognitia.abi.types import current_utc_timestamp
from cognitia.learning.contract import (
    AdaptiveLearningFailure,
    CandidateStatus,
    KnowledgeType,
    LearningDomain,
    LearningTransferProposal,
    ModelCandidate,
    TransferCompatibilityResult,
    TransferCompatibilityStatus,
    TransferType,
)
from cognitia.models.registry import ModelRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType


class LearningTransferEngine:
    """Engine assessing cross-domain compatibility and instantiating advisory transfer candidates."""

    @classmethod
    def evaluate_compatibility(
        cls,
        proposal: LearningTransferProposal | None = None,
        source_domain: LearningDomain | None = None,
        target_domain: LearningDomain | None = None,
        source_model_id: str = "",
        source_model_version: str = "1.0.0",
        source_provider_id: str = "laya",
        target_provider_id: str = "laya",
        source_representation_version: str | None = None,
        target_representation_version: str | None = None,
        transfer_type: TransferType = TransferType.PARAMETER_TRANSFER,
        knowledge_type: KnowledgeType = KnowledgeType.MODEL_CANDIDATE,
    ) -> TransferCompatibilityResult:
        """Evaluate representation, provider, and domain compatibility for knowledge transfer.
        
        Advisory only; authority is strictly NONE.
        """
        if proposal is not None:
            source_model_id = proposal.source_model_id or source_model_id
            source_model_version = proposal.source_model_version or source_model_version
            source_provider_id = proposal.source_provider_id or source_provider_id
            target_provider_id = proposal.target_provider_id or target_provider_id
            transfer_type = proposal.transfer_type or transfer_type
            knowledge_type = proposal.knowledge_type or knowledge_type

        src_id = source_domain.domain_id if source_domain else (proposal.source_domain_id if proposal else "unknown")
        tgt_id = target_domain.domain_id if target_domain else (proposal.target_domain_id if proposal else "unknown")

        reasons: list[str] = []
        risks: list[str] = []
        validation_reqs: list[str] = [
            "target_domain_dataset_evaluation",
            "domain_governance_authorization",
        ]

        if source_domain is not None:
            src_rep_ver = source_domain.representation_version
        elif source_representation_version is not None:
            src_rep_ver = source_representation_version
        elif proposal is not None and proposal.source_representation_version:
            src_rep_ver = proposal.source_representation_version
        else:
            src_rep_ver = "1.0.0"

        if target_domain is not None:
            tgt_rep_ver = target_domain.representation_version
        elif target_representation_version is not None:
            tgt_rep_ver = target_representation_version
        elif proposal is not None and proposal.target_representation_version:
            tgt_rep_ver = proposal.target_representation_version
        else:
            tgt_rep_ver = "1.0.0"


        # 1. Domain Separation Check
        if src_id == tgt_id:
            return TransferCompatibilityResult(
                proposal_id=proposal.id if proposal else "",
                source_domain_id=src_id,
                target_domain_id=tgt_id,
                is_compatible=False,
                status=TransferCompatibilityStatus.INCOMPATIBLE,
                compatibility_status=TransferCompatibilityStatus.INCOMPATIBLE,
                score=0.0,
                representation_compatible=True,
                provider_compatible=True,
                domain_separation_verified=False,
                reasons=["Source and target domains must be distinct for cross-domain transfer."],
                risks=["Self-transfer invalidates domain isolation boundaries."],
                advisory_recommendation="Reject transfer proposal: source and target domains are identical.",
                authority="NONE",
            )

        # 2. Representation Compatibility Check
        src_major = src_rep_ver.split(".")[0]
        tgt_major = tgt_rep_ver.split(".")[0]

        if src_rep_ver == tgt_rep_ver:
            rep_compat = True
            reasons.append(f"Representation versions match exactly: {src_rep_ver}")
        elif src_major == tgt_major:
            rep_compat = True
            reasons.append(f"Representation minor version difference compatible: {src_rep_ver} -> {tgt_rep_ver}")
        else:
            rep_compat = False
            reasons.append(f"Representation major version mismatch: {src_rep_ver} incompatible with {tgt_rep_ver}")
            risks.append(f"Major representation version mismatch ({src_rep_ver} vs {tgt_rep_ver}) may cause semantic distortion.")

        # 3. Provider Compatibility Check
        if source_provider_id == target_provider_id:
            prov_compat = True
            reasons.append(f"Provider match confirmed: '{source_provider_id}' -> '{target_provider_id}'")
        else:
            prov_compat = False
            reasons.append(
                f"Provider mismatch: '{source_provider_id}' cannot transfer parameters directly to '{target_provider_id}' without cross-provider adapter"
            )
            risks.append(f"Different model architectures between providers ({source_provider_id} vs {target_provider_id}).")

        # 4. Synthesize Status & Score
        if rep_compat and prov_compat:
            status = TransferCompatibilityStatus.COMPATIBLE
            is_compat = True
            score = 0.95
            advisory_rec = "Compatible for target candidate creation. External evaluation recommended."
        elif rep_compat and not prov_compat and transfer_type in (TransferType.STATISTICAL_PRIOR, TransferType.FEATURE_EXTRACTOR_TRANSFER):
            status = TransferCompatibilityStatus.PARTIALLY_COMPATIBLE
            is_compat = True
            score = 0.65
            validation_reqs.append("cross_provider_parameter_translation")
            reasons.append("Transfer partially compatible across distinct providers under feature/statistical prior translation.")
            advisory_rec = "Partially compatible: Requires target domain adapter validation before promotion proposal."
        else:
            status = TransferCompatibilityStatus.INCOMPATIBLE
            is_compat = False
            score = 0.15
            advisory_rec = "Incompatible: Transfer proposal should be rejected by domain governance."

        prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"transfer_engine:compat:{src_id}->{tgt_id}",
            capability_id="learn.adaptive.transfer",
            is_deterministic=True,
        )

        compat_details = {
            "source_domain_id": src_id,
            "target_domain_id": tgt_id,
            "source_representation_version": src_rep_ver,
            "target_representation_version": tgt_rep_ver,
            "source_provider_id": source_provider_id,
            "target_provider_id": target_provider_id,
            "transfer_type": transfer_type.value if hasattr(transfer_type, "value") else str(transfer_type),
        }

        return TransferCompatibilityResult(
            proposal_id=proposal.id if proposal else "",
            source_domain_id=src_id,
            target_domain_id=tgt_id,
            is_compatible=is_compat,
            status=status,
            compatibility_status=status,
            score=score,
            representation_compatible=rep_compat,
            provider_compatible=prov_compat,
            domain_separation_verified=True,
            compatibility_details=compat_details,
            risks=risks,
            reasons=reasons,
            validation_requirements=validation_reqs,
            advisory_recommendation=advisory_rec,
            authority="NONE",
            provenance=prov,
        )

    @classmethod
    def create_proposal(
        cls,
        source_domain: LearningDomain,
        target_domain: LearningDomain,
        source_model_id: str,
        source_model_version: str = "1.0.0",
        target_model_id: str | None = None,
        target_base_model_version: str = "1.0.0",
        source_candidate_version: str | None = None,
        source_provider_id: str = "laya",
        target_provider_id: str = "laya",
        source_representation_version: str | None = None,
        target_representation_version: str | None = None,
        transfer_type: TransferType = TransferType.MODEL_TRANSFER,
        knowledge_type: KnowledgeType = KnowledgeType.FEATURE_EXTRACTOR,
        rationale: str = "",
        transfer_payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[LearningTransferProposal, TransferCompatibilityResult]:
        """Generate an explicit LearningTransferProposal and its compatibility evaluation."""
        tgt_model_id = target_model_id or source_model_id

        compat = cls.evaluate_compatibility(
            source_domain=source_domain,
            target_domain=target_domain,
            source_model_id=source_model_id,
            source_model_version=source_model_version,
            source_provider_id=source_provider_id,
            target_provider_id=target_provider_id,
            source_representation_version=source_representation_version,
            target_representation_version=target_representation_version,
            transfer_type=transfer_type,
            knowledge_type=knowledge_type,
        )

        proposal_status = "PROPOSED" if compat.is_compatible else "REJECTED"

        proposal_prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"transfer_engine:proposal:{source_domain.domain_id}->{target_domain.domain_id}",
            capability_id="learn.adaptive.transfer",
            is_deterministic=True,
        )

        proposal = LearningTransferProposal(
            source_domain_id=source_domain.domain_id,
            target_domain_id=target_domain.domain_id,
            source_model_id=source_model_id,
            source_model_version=source_model_version,
            target_model_id=tgt_model_id,
            target_base_model_version=target_base_model_version,
            source_candidate_version=source_candidate_version,
            source_representation_version=source_representation_version or source_domain.representation_version,
            target_representation_version=target_representation_version or target_domain.representation_version,
            source_provider_id=source_provider_id,
            target_provider_id=target_provider_id,
            transfer_type=transfer_type,
            knowledge_type=knowledge_type,
            compatibility_status=compat.status,
            compatibility_reasons=compat.reasons,
            validation_requirements=compat.validation_requirements,
            rationale=rationale or f"Cross-domain transfer proposal from {source_domain.domain_id} to {target_domain.domain_id}",
            transfer_payload=transfer_payload or {},
            status=proposal_status,
            authority="NONE",
            provenance=proposal_prov,
            metadata=metadata or {},
        )

        # Link proposal id into compatibility result
        if not compat.proposal_id:
            object.__setattr__(compat, "proposal_id", proposal.id)

        return proposal, compat

    @classmethod
    def instantiate_transfer_candidate(
        cls,
        proposal: LearningTransferProposal,
        source_candidate: ModelCandidate | None,
        source_model_record: ModelRecord,
        target_model_id: str | None = None,
        target_candidate_version: str | None = None,
        seed: int = 42,
    ) -> ModelCandidate:
        """Create a new target-domain ModelCandidate from an authorized transfer proposal.
        
        CRITICAL ARCHITECTURAL CONTRACT:
        Creates a new candidate only. Never modifies, overwrites, replaces, activates,
        or mutates the target domain's active model.
        """
        tgt_model_id = target_model_id or proposal.target_model_id or proposal.source_model_id
        target_domain_id = proposal.target_domain_id or proposal.target_domain

        if proposal.compatibility_status == TransferCompatibilityStatus.INCOMPATIBLE:
            raise AdaptiveLearningFailure(
                f"Cannot instantiate transfer candidate: Proposal '{proposal.id}' is INCOMPATIBLE ({proposal.compatibility_reasons})",
                model_id=tgt_model_id,
                domain_id=target_domain_id,
                error_code="INCOMPATIBLE_TRANSFER",
            )

        if proposal.status == "REJECTED":
            raise AdaptiveLearningFailure(
                f"Cannot instantiate transfer candidate: Proposal '{proposal.id}' was REJECTED",
                model_id=tgt_model_id,
                domain_id=target_domain_id,
                error_code="REJECTED_TRANSFER",
            )

        # Candidate parameters and fingerprint derived from source + transfer payload
        cand_params = dict(source_candidate.parameters) if source_candidate else {
            "source_model": source_model_record.model_id,
            "source_version": source_model_record.model_version,
            "transfer_seed": seed,
        }
        if proposal.transfer_payload:
            cand_params.update(proposal.transfer_payload)

        # Provenance linkage: lineage explicitly identifies source transfer proposal and source domain
        cand_params["source_transfer_proposal_id"] = proposal.id
        cand_params["source_domain_id"] = proposal.source_domain_id or proposal.source_domain

        param_canonical = json.dumps(cand_params, sort_keys=True)
        param_fingerprint = hashlib.sha256(param_canonical.encode("utf-8")).hexdigest()

        # Clean candidate version scoped to target domain
        target_cand_ver = target_candidate_version or f"{tgt_model_id}:transfer-from-{proposal.source_domain_id}.1-candidate"

        prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"transfer_engine:candidate:{target_domain_id}:{tgt_model_id}",
            capability_id="learn.adaptive.transfer",
            is_deterministic=True,
        )

        return ModelCandidate(
            domain_id=target_domain_id,
            candidate_model_id=tgt_model_id,
            candidate_model_version=target_cand_ver,
            parent_model_id=source_model_record.model_id,
            parent_model_version=source_model_record.model_version,
            provider_id=proposal.target_provider_id,
            provider_version="1.0.0",
            status=CandidateStatus.CANDIDATE,
            parameter_fingerprint=param_fingerprint,
            parameters=cand_params,
            creation_seed=seed,
            transfer_proposal_id=proposal.id,
            is_deterministic=True,
            authority="NONE",
            provenance=prov,
        )

