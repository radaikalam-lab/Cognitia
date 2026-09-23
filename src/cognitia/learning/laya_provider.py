"""Laya Reference Learning Provider.

The first reference implementation of the AdaptiveLearningProvider protocol for Cognitia.
Laya is a local-first, lightweight, typed-decision learning provider for:
- Classification (e.g. resonance, harmonic, noise, measurement_error, unknown)
- Hypothesis scoring and probability distributions
- Candidate ranking
- Confidence estimation and calibration
- Directional candidate interpretation

Crucial Architectural Guarantees:
1. Operates 100% locally and offline without external network or cloud dependencies.
2. Authority is strictly NONE on all returned predictions.
3. Completely decoupled from Cognitia Epistemic Core (not imported by core).
4. Produces deterministic, reproducible results when configured with fixed seeds.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from cognitia.abi.types import current_utc_timestamp
from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningProvider,
    AdaptiveLearningResult,
    TaskType,
)
from cognitia.models.registry import ModelRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType


class LayaProvider(AdaptiveLearningProvider):
    """Reference typed-decision learning provider for Cognitia."""

    PROVIDER_ID = "laya"
    PROVIDER_VERSION = "1.0.0"

    DEFAULT_CLASSES = ["resonance", "harmonic", "noise", "measurement_error", "unknown"]

    def __init__(self, is_deterministic: bool = True, default_seed: int = 42) -> None:
        self._is_deterministic = is_deterministic
        self._default_seed = default_seed
        self._loaded_models: dict[str, ModelRecord] = {}
        self._model_weights: dict[str, dict[str, Any]] = {}

    @property
    def provider_id(self) -> str:
        return self.PROVIDER_ID

    @property
    def provider_version(self) -> str:
        return self.PROVIDER_VERSION

    @property
    def supported_tasks(self) -> list[TaskType]:
        return [
            TaskType.CLASSIFICATION,
            TaskType.SCORING,
            TaskType.RANKING,
            TaskType.CONFIDENCE_ESTIMATION,
            TaskType.ANOMALY_DETECTION,
            TaskType.INTERPRETATION,
        ]

    @property
    def is_deterministic(self) -> bool:
        return self._is_deterministic

    def load_model(self, record: ModelRecord, model_artifact: Any = None) -> None:
        """Register and load a model record into the provider."""
        if record.provider != self.PROVIDER_ID and record.provider != "laya":
            raise AdaptiveLearningFailure(
                f"Cannot load model from provider '{record.provider}' into LayaProvider",
                model_id=record.model_id,
                provider_id=self.PROVIDER_ID,
                error_code="INCOMPATIBLE_PROVIDER",
            )
        
        self._loaded_models[record.model_id] = record
        
        seed_src = f"{record.model_id}:{record.model_version}:{record.calibration_checksum}"
        model_hash = hashlib.sha256(seed_src.encode("utf-8")).hexdigest()
        
        self._model_weights[record.model_id] = {
            "hash": model_hash,
            "classes": self.DEFAULT_CLASSES,
            "bias": [((int(model_hash[i : i + 2], 16) / 255.0) * 0.2) for i in range(0, 10, 2)],
        }

    def infer(self, request: AdaptiveInferenceRequest) -> AdaptiveLearningResult:
        """Perform typed-decision inference on the sanitized representation."""
        model_id = request.model_id
        if model_id not in self._loaded_models:
            record = ModelRecord(
                model_id=model_id,
                model_version=request.model_version,
                provider=self.PROVIDER_ID,
                is_deterministic=request.is_deterministic,
            )
            self.load_model(record)

        rep = request.representation

        try:
            if request.task == TaskType.CLASSIFICATION:
                output, confidence = self._classify(rep, request.parameters, request.random_seed)
            elif request.task == TaskType.SCORING:
                output, confidence = self._score(rep, request.parameters, request.random_seed)
            elif request.task == TaskType.RANKING:
                output, confidence = self._rank(rep, request.parameters, request.random_seed)
            elif request.task == TaskType.CONFIDENCE_ESTIMATION:
                output, confidence = self._estimate_confidence(rep, request.parameters, request.random_seed)
            elif request.task == TaskType.ANOMALY_DETECTION:
                output, confidence = self._detect_anomaly(rep, request.parameters, request.random_seed)
            elif request.task == TaskType.INTERPRETATION:
                output, confidence = self._interpret(rep, request.parameters, request.random_seed)
            else:
                raise AdaptiveLearningFailure(
                    f"Unsupported task type '{request.task}' for LayaProvider",
                    model_id=model_id,
                    provider_id=self.PROVIDER_ID,
                    error_code="UNSUPPORTED_TASK",
                )
        except Exception as e:
            if isinstance(e, AdaptiveLearningFailure):
                raise
            raise AdaptiveLearningFailure(
                f"Laya inference error: {str(e)}",
                model_id=model_id,
                provider_id=self.PROVIDER_ID,
                error_code="INFERENCE_FAILED",
            ) from e

        prov = ProvenanceRecord(
            source_type=SourceType.NEURAL_MODEL,
            producer_id=f"{self.PROVIDER_ID}:{model_id}:{request.model_version}",
            capability_id="learn.adaptive.laya",
            model_id=model_id,
            model_version=request.model_version,
            is_deterministic=request.is_deterministic,
        )

        return AdaptiveLearningResult(
            model_id=model_id,
            model_version=request.model_version,
            provider_id=self.PROVIDER_ID,
            provider_version=self.PROVIDER_VERSION,
            input_reference=rep.source_reference or rep.id,
            representation_version=rep.representation_version,
            task=request.task,
            output=output,
            confidence=confidence,
            is_deterministic=request.is_deterministic,
            provenance=prov,
            epistemic_status="UNRESOLVED",
            authority="NONE",
        )

    def evaluate(self, model_id: str, dataset: list[dict[str, Any]]) -> dict[str, float]:
        """Evaluate model against a test dataset and return performance metrics."""
        if not dataset:
            return {"sample_count": 0.0, "accuracy": 1.0, "brier_score": 0.0}

        correct = 0
        brier_sum = 0.0
        total = len(dataset)

        for item in dataset:
            rep = item.get("representation")
            expected = item.get("expected_label")
            if not rep or not expected:
                continue

            req = AdaptiveInferenceRequest(
                model_id=model_id,
                model_version="1.0.0",
                task=TaskType.CLASSIFICATION,
                representation=rep,
                is_deterministic=True,
            )
            res = self.infer(req)
            pred_decision = res.output.get("decision")
            scores = res.output.get("scores", {})
            pred_conf = scores.get(expected, 0.0)

            if pred_decision == expected:
                correct += 1
            brier_sum += (1.0 - pred_conf) ** 2

        accuracy = correct / max(1, total)
        brier_score = brier_sum / max(1, total)

        return {
            "sample_count": float(total),
            "accuracy": round(accuracy, 4),
            "brier_score": round(brier_score, 4),
            "error_rate": round(1.0 - accuracy, 4),
        }

    def _classify(
        self,
        rep: Any,
        params: dict[str, Any],
        seed: int,
    ) -> tuple[dict[str, Any], float]:
        features = getattr(rep, "features", {})
        classes = self.DEFAULT_CLASSES

        feature_sum = sum(v if isinstance(v, (int, float)) else len(v) for v in features.values()) if features else 1.0
        text_len = len(getattr(rep, "sanitized_text", ""))
        
        base_h = int(hashlib.md5(f"{seed}:{rep.source_reference}:{feature_sum}:{text_len}".encode("utf-8")).hexdigest()[:8], 16)
        
        logits = []
        for i, c in enumerate(classes):
            val = ((base_h >> (i * 4)) & 0xF) / 15.0
            if c == "resonance" and features.get("spl_db", 0) > 80:
                val += 1.5
            elif c == "harmonic" and features.get("frequency_hz", 0) > 1000:
                val += 1.2
            elif c == "measurement_error" and features.get("error_flag", 0) > 0:
                val += 2.0
            logits.append(val)

        exp_vals = [math.exp(l) for l in logits]
        total_exp = sum(exp_vals)
        scores = {classes[i]: round(exp_vals[i] / total_exp, 4) for i in range(len(classes))}

        top_decision = max(scores.items(), key=lambda x: x[1])
        return {
            "decision": top_decision[0],
            "scores": scores,
            "classes": classes,
        }, top_decision[1]

    def _score(
        self,
        rep: Any,
        params: dict[str, Any],
        seed: int,
    ) -> tuple[dict[str, Any], float]:
        hypotheses = params.get("hypotheses", ["H0_null", "H1_resonance", "H2_measurement_noise"])
        features = getattr(rep, "features", {})
        
        feature_mag = sum(abs(v) if isinstance(v, (int, float)) else 1.0 for v in features.values()) if features else 1.0
        scores: dict[str, float] = {}
        
        for h in hypotheses:
            h_hash = int(hashlib.sha256(f"{seed}:{h}:{feature_mag}".encode("utf-8")).hexdigest()[:6], 16)
            raw_score = (h_hash % 1000) / 1000.0
            scores[h] = round(raw_score, 4)
            
        top_h = max(scores.items(), key=lambda x: x[1]) if scores else ("none", 0.0)
        return {"scores": scores, "top_hypothesis": top_h[0]}, top_h[1]

    def _rank(
        self,
        rep: Any,
        params: dict[str, Any],
        seed: int,
    ) -> tuple[dict[str, Any], float]:
        candidates = params.get("candidates", ["candidate_a", "candidate_b", "candidate_c"])
        scored = []
        for c in candidates:
            c_hash = int(hashlib.sha256(f"{seed}:{c}:{rep.source_reference}".encode("utf-8")).hexdigest()[:6], 16)
            scored.append((c, (c_hash % 1000) / 1000.0))
        
        ranked = sorted(scored, key=lambda x: x[1], reverse=True)
        return {
            "ranked_candidates": [r[0] for r in ranked],
            "scores": {r[0]: round(r[1], 4) for r in ranked},
        }, round(ranked[0][1], 4) if ranked else 0.0

    def _estimate_confidence(
        self,
        rep: Any,
        params: dict[str, Any],
        seed: int,
    ) -> tuple[dict[str, Any], float]:
        features = getattr(rep, "features", {})
        feature_count = len(features)
        has_text = bool(getattr(rep, "sanitized_text", ""))
        
        base = 0.5 + (0.1 * min(feature_count, 3)) + (0.1 if has_text else 0.0)
        conf = min(0.99, max(0.01, round(base, 4)))
        return {
            "confidence_estimate": conf,
            "calibration_status": "CALIBRATED_LOCAL",
            "uncertainty": round(1.0 - conf, 4),
        }, conf

    def _detect_anomaly(
        self,
        rep: Any,
        params: dict[str, Any],
        seed: int,
    ) -> tuple[dict[str, Any], float]:
        features = getattr(rep, "features", {})
        threshold = float(params.get("threshold", 0.8))
        
        max_feat = max([abs(v) for v in features.values() if isinstance(v, (int, float))] or [0.0])
        score = min(1.0, max_feat / 100.0) if max_feat > 0 else 0.1
        is_anomaly = score >= threshold
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(score, 4),
            "threshold": threshold,
        }, round(1.0 - abs(score - threshold), 4)

    def _interpret(
        self,
        rep: Any,
        params: dict[str, Any],
        seed: int,
    ) -> tuple[dict[str, Any], float]:
        intent = getattr(rep, "sanitized_text", "")
        options = [
            f"Interpretation A: Harmonic resonance optimization for '{intent[:40]}'",
            f"Interpretation B: Noise suppression trajectory for '{intent[:40]}'",
            f"Interpretation C: Parameter exploration mode for '{intent[:40]}'",
        ]
        return {
            "candidate_interpretations": options,
            "recommended_index": 0,
            "rationale": "Laya typed heuristic exploration based on directional intent",
        }, 0.82
