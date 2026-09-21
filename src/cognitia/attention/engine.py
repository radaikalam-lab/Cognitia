"""Cognitia Attention Engine and SPI.

Implements provider-neutral deterministic attention prioritization over CognitiveContext.
All results are immutable snapshots containing ranked references and explainable selection reasons.
"""

from __future__ import annotations

import datetime
from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import (
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.context.types import (
    CognitiveContext,
    ContextItem,
    RelevanceReason,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType

from cognitia.attention.types import (
    AttentionItem,
    AttentionQuery,
    AttentionReason,
    AttentionResult,
)


@runtime_checkable
class AttentionEngine(Protocol):
    """Protocol for provider-neutral cognitive attention prioritization."""

    def focus(
        self,
        context: CognitiveContext,
        query: AttentionQuery | None = None,
    ) -> AttentionResult:
        """Focus and prioritize information from an assembled CognitiveContext."""
        ...


def _parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    """Safely parse ISO timestamp into timezone-aware datetime."""
    try:
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


class DeterministicAttentionEngine:
    """Deterministic reference implementation of AttentionEngine.
    
    INVARIANTS:
    1. Does NOT duplicate Context, Persistence, or Memory objects (stores immutable references only).
    2. Deterministic ranking and stable tie-breaking: (score desc, timestamp desc, item_id asc).
    3. Produces deeply immutable AttentionResult snapshots.
    4. Preserves epistemic tension; contradictory evidence is not suppressed.
    5. Attention score is strictly a deterministic prioritization value, NOT confidence or truth.
    """

    def focus(
        self,
        context: CognitiveContext,
        query: AttentionQuery | None = None,
    ) -> AttentionResult:
        """Prioritize and focus context items into a ranked attention snapshot."""
        q = query or AttentionQuery()

        scored_candidates: list[tuple[float, str, float, ContextItem, list[AttentionReason]]] = []
        deltas_map = context.temporal_context.deltas_dict
        ref_timestamp_str = context.temporal_context.reference_timestamp or context.created_at

        # Resolve focus subjects
        focus_subjects = set(q.focus_subject_ids)
        explicit_item_ids = set()
        if "explicit_item_ids" in q.parameters_dict:
            explicit_val = q.parameters_dict["explicit_item_ids"]
            if isinstance(explicit_val, (list, tuple, set)):
                explicit_item_ids.update(explicit_val)

        requested_types = {t.lower() for t in q.requested_item_types} if q.requested_item_types else None

        for item in context.context_items:
            # 1. Type filtering if specified
            if requested_types and item.item_type.lower() not in requested_types and item.item_type not in q.requested_item_types:
                continue

            # 2. Epistemic status check
            item_ep_status = item.epistemic_status or context.epistemic_map.get(item.item_id)
            if q.target_epistemic_statuses and item_ep_status not in q.target_epistemic_statuses:
                continue

            # 3. Deterministic scoring and explainable reasons collection
            reasons: list[AttentionReason] = []
            score = item.relevance_score * 0.35

            # Reference item match
            if item.item_id == context.reference_observation_id:
                reasons.append(AttentionReason.REFERENCE_ITEM)
                score += 0.30

            # Subject match
            if focus_subjects:
                if (
                    context.reference_subject_id in focus_subjects
                    or item.item_id in focus_subjects
                    or (hasattr(item, "subject_id") and getattr(item, "subject_id") in focus_subjects)
                ):
                    reasons.append(AttentionReason.SUBJECT_MATCH)
                    score += 0.35
            elif item.relevance_reason == RelevanceReason.SUBJECT_MATCH:
                reasons.append(AttentionReason.SUBJECT_MATCH)
                score += 0.15

            # Task-specific match
            if q.task_type == "anomaly_investigation":
                if item_ep_status in (EpistemicStatus.REFUTED, EpistemicStatus.UNRESOLVED) or item.item_type.lower() in ("residual", "challenge"):
                    reasons.append(AttentionReason.TASK_MATCH)
                    score += 0.40
                elif item.relevance_reason in (RelevanceReason.REFERENCE_OBSERVATION, RelevanceReason.TEMPORAL_MATCH):
                    reasons.append(AttentionReason.TASK_MATCH)
                    score += 0.05
            elif q.task_type == "trend_analysis":
                if item.relevance_reason == RelevanceReason.TEMPORAL_MATCH or item.item_type.lower() in ("observation", "measurerecord"):
                    reasons.append(AttentionReason.TASK_MATCH)
                    score += 0.40
            elif q.task_type == "rule_evaluation":
                if item.relevance_reason == RelevanceReason.RULE_MATCH or item.item_type.lower() in ("cognitiverule", "rule") or item.item_id in context.active_rule_ids:
                    reasons.append(AttentionReason.TASK_MATCH)
                    score += 0.40
            elif q.task_type in ("memory_retrieval", "historical_audit"):
                if item.relevance_reason == RelevanceReason.MEMORY_MATCH or item.item_type.lower() in ("experiencerecord", "experience", "claim"):
                    reasons.append(AttentionReason.TASK_MATCH)
                    score += 0.40
            elif q.task_type == "epistemic_audit":
                if item_ep_status is not None:
                    reasons.append(AttentionReason.TASK_MATCH)
                    score += 0.40
            else:
                reasons.append(AttentionReason.TASK_MATCH)
                score += 0.10

            # Context Relevance Reason mapping
            if item.relevance_reason == RelevanceReason.TEMPORAL_MATCH:
                reasons.append(AttentionReason.TEMPORAL_PROXIMITY)
                score += 0.10
            elif item.relevance_reason == RelevanceReason.EPISODE_MATCH:
                reasons.append(AttentionReason.EPISODE_RELEVANCE)
                score += 0.15
            elif item.relevance_reason == RelevanceReason.RULE_MATCH or item.item_type.lower() in ("cognitiverule", "rule") or item.item_id in context.active_rule_ids:
                reasons.append(AttentionReason.RULE_RELEVANCE)
                score += 0.15
            elif item.relevance_reason == RelevanceReason.MEMORY_MATCH or item.item_type.lower() in ("experiencerecord", "experience"):
                reasons.append(AttentionReason.MEMORY_RELEVANCE)
                score += 0.15
            elif item.relevance_reason == RelevanceReason.SOURCE_MATCH:
                reasons.append(AttentionReason.SOURCE_RELEVANCE)
                score += 0.10

            # Epistemic relevance
            if item_ep_status is not None:
                reasons.append(AttentionReason.EPISTEMIC_RELEVANCE)
                if q.target_epistemic_statuses and item_ep_status in q.target_epistemic_statuses:
                    score += 0.35
                else:
                    score += 0.10

            # Explicit item selection
            if item.item_id in explicit_item_ids:
                reasons.append(AttentionReason.EXPLICIT_SELECTION)
                score += 0.50

            # Normalize score to [0.0, 1.0]
            normalized_score = min(1.0, max(0.0, score))
            rounded_score = round(normalized_score, 6)

            # Minimum score threshold check
            if rounded_score < q.minimum_score:
                continue

            # Deduplicate reasons preserving insertion order
            unique_reasons = tuple(dict.fromkeys(reasons))
            if not unique_reasons:
                unique_reasons = (AttentionReason.TASK_MATCH,)

            # Determine timestamp for stable tie-breaking
            time_delta = deltas_map.get(item.item_id, 0.0)
            item_ts = ref_timestamp_str

            scored_candidates.append((rounded_score, item_ts, time_delta, item, list(unique_reasons)))

        # 4. Deterministic Stable Tie-Breaking:
        # Sort Key: (score DESC, time_delta DESC, item_ts DESC, item_id ASC)
        scored_candidates.sort(
            key=lambda c: (
                -c[0],               # attention_score DESC
                -c[2],               # time_delta DESC (closer to zero or positive)
                c[1],                # timestamp
                c[3].item_id,        # item_id ASC
            )
        )

        # 5. Attention Budget Enforcement
        selected_candidates = scored_candidates[: q.maximum_items]

        # 6. Build AttentionItems with 1-indexed ranks
        attention_items: list[AttentionItem] = []
        selected_ids: list[str] = []

        for idx, (score, _, _, ctx_item, reasons_list) in enumerate(selected_candidates, start=1):
            ep_status = ctx_item.epistemic_status or context.epistemic_map.get(ctx_item.item_id)
            att_item = AttentionItem(
                item_id=ctx_item.item_id,
                rank=idx,
                attention_score=score,
                source_context_item_id=ctx_item.item_id,
                selection_reasons=reasons_list,
                epistemic_status=ep_status,
                metadata={
                    "source_context_id": context.id,
                    "item_type": ctx_item.item_type,
                    "context_relevance_reason": ctx_item.relevance_reason.value,
                },
            )
            attention_items.append(att_item)
            selected_ids.append(ctx_item.item_id)

        # 7. Build Provenance Record
        parent_ids = [context.provenance.id, context.id] + selected_ids
        prov = ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id="deterministic_attention_engine",
            parent_ids=parent_ids,
            is_deterministic=True,
        )

        # 8. Produce Frozen AttentionResult
        return AttentionResult(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            reference_observation_id=context.reference_observation_id,
            context_id=context.id,
            task_id=q.task_id,
            task_type=q.task_type,
            selected_item_ids=tuple(selected_ids),
            attention_items=tuple(attention_items),
            budget_limit=q.maximum_items,
            provenance=prov,
            metadata={
                "source_application": context.metadata.get("source_application"),
                "episode_id": context.metadata.get("episode_id"),
                "scope": q.scope or context.metadata.get("scope"),
            },
        )
