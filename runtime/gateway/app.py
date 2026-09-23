"""Cognitia Standalone Runtime - Local-First Gateway Application.

Lightweight HTTP Gateway exposing Provider Registry, Epistemic Ingestion, and
Directional Programming Proposal evaluation with Durable File Persistence.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .abi_validator import (
    ABIValidationError,
    ABIValidator,
    RuntimeValidationError,
)
from .epistemic_bridge import (
    EpistemicBridge,
    EpistemicCapacityExceededError,
)
from .provider_registry import ProviderRegistry
from .security import (
    RateLimiter,
    SecuritySanitizer,
    SecurityValidationError,
)
from ..persistence.file_persistence import FilePersistenceService
from ..persistence.persistence_contract import (
    DurabilityMode,
    PersistenceError,
    PersistenceWriteError,
)

logger = logging.getLogger("cognitia.runtime.gateway")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

MAX_BODY_SIZE = 512 * 1024  # 512 KB


class CognitiaGatewayHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Cognitia Provider Gateway."""

    provider_registry: ProviderRegistry
    rate_limiter: RateLimiter
    epistemic_bridge: EpistemicBridge

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        response_bytes = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("X-Cognitia-Runtime-Version", "1.0.0")
        self.send_header("X-Cognitia-ABI-Version", "1.0.0")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _send_error(
        self,
        status: HTTPStatus,
        error_type: str,
        message: str,
        correlation_id: str | None = None,
    ) -> None:
        payload = {
            "error": True,
            "error_type": error_type,
            "error_code": error_type,
            "message": message,
            "authority": "NONE",
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._send_json(status, payload)

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/")

        if path == "/v1/health":
            status_summary = self.epistemic_bridge.get_status_summary()
            pers_health = status_summary.get("persistence", {})
            is_healthy = pers_health.get("healthy", True) if pers_health.get("enabled", False) else True

            health_payload = {
                "status": "healthy" if is_healthy else "unhealthy",
                "runtime_identity": "Cognitia",
                "runtime_version": "1.0.0",
                "cognitive_abi_version": "1.0.0",
                "protocol_version": "1.0.0",
                "authority_model": "NONE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "epistemic": {
                    "status": "available",
                    "active_nodes": status_summary["active_nodes_count"],
                    "max_capacity": status_summary["max_node_capacity"],
                },
                "persistence": pers_health,
            }
            status_code = HTTPStatus.OK if is_healthy else HTTPStatus.SERVICE_UNAVAILABLE
            self._send_json(status_code, health_payload)

        elif path == "/v1/capabilities":
            capabilities = [
                {
                    "capability": "learn.adaptive",
                    "description": "Advisory adaptive machine learning and typed decision inference",
                    "direction": "INBOUND_ADVISORY",
                    "provider": "laya",
                    "is_deterministic": True,
                    "authority": "NONE",
                },
                {
                    "capability": "observe.navigation",
                    "description": "Passive browser navigation lifecycle telemetry observation",
                    "direction": "INBOUND",
                    "authority": "NONE",
                },
                {
                    "capability": "observe.authorized_content",
                    "description": "Explicit user-authorized webpage content extraction observation",
                    "direction": "INBOUND",
                    "authority": "NONE",
                },
                {
                    "capability": "observe.generic",
                    "description": "General sensor/telemetry observation ingestion",
                    "direction": "INBOUND",
                    "authority": "NONE",
                },
                {
                    "capability": "propose.directional",
                    "description": "Directional specification evaluation and advisory candidate proposals",
                    "direction": "OUTBOUND_ADVISORY",
                    "authority": "NONE",
                },
                {
                    "capability": "persistence.file",
                    "description": "Durable local-first file persistence and crash recovery",
                    "direction": "INTERNAL_STORAGE",
                    "authority": "NONE",
                },
            ]
            self._send_json(HTTPStatus.OK, {"capabilities": capabilities})

        elif path == "/v1/learning/models":
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(self.path).query)
            d_id = query.get("domain_id", ["default"])[0]
            models = self.epistemic_bridge.adaptive_learning.model_registry.list_by_domain(d_id)
            if not models:
                models = self.epistemic_bridge.adaptive_learning.model_registry.list_versions("laya_acoustic_v1")
            active_rec = self.epistemic_bridge.adaptive_learning.model_registry.get_active(domain_id=d_id)
            model_list = [
                {
                    "model_id": m.model_id,
                    "model_version": m.model_version,
                    "domain_id": m.domain_id,
                    "provider": m.provider,
                    "is_deterministic": m.is_deterministic,
                    "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                    "lifecycle_state": m.lifecycle_state.value if hasattr(m.lifecycle_state, "value") else str(m.lifecycle_state),
                    "runtime_activation_state": m.runtime_activation_state.value if hasattr(m.runtime_activation_state, "value") else str(m.runtime_activation_state),
                    "task_type": m.task_type,
                    "model_role": m.model_role,
                }
                for m in models
            ] or [
                {
                    "model_id": "laya_acoustic_v1",
                    "model_version": "1.0.0",
                    "domain_id": d_id,
                    "provider": "laya",
                    "is_deterministic": True,
                    "status": "active",
                    "lifecycle_state": "active",
                    "runtime_activation_state": "not_active",
                    "task_type": "classification",
                    "model_role": "primary",
                }
            ]
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "provider": "laya",
                    "active_model": active_rec.model_id if active_rec else "laya_acoustic_v1",
                    "available_models": model_list,
                    "models": model_list,
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/history":
            history = self.epistemic_bridge.adaptive_learning.list_history()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(history),
                    "results": [
                        {
                            "id": r.id,
                            "model_id": r.model_id,
                            "model_version": r.model_version,
                            "provider_id": r.provider_id,
                            "task": r.task.value if hasattr(r.task, "value") else str(r.task),
                            "output": r.output,
                            "confidence": r.confidence,
                            "is_deterministic": r.is_deterministic,
                            "authority": r.authority,
                            "epistemic_status": r.epistemic_status,
                        }
                        for r in history
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/drift":
            reports = self.epistemic_bridge.adaptive_learning.list_drift_reports()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(reports),
                    "reports": [
                        {
                            "id": rep.id,
                            "model_id": rep.model_id,
                            "drift_type": rep.drift_type.value if hasattr(rep.drift_type, "value") else str(rep.drift_type),
                            "metric_name": rep.metric_name,
                            "baseline_value": rep.baseline_value,
                            "current_value": rep.current_value,
                            "drift_magnitude": rep.drift_magnitude,
                            "drift_detected": rep.drift_detected,
                            "recommendation": rep.recommendation,
                            "authority": rep.authority,
                        }
                        for rep in reports
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/outcomes":
            outcomes = self.epistemic_bridge.adaptive_learning.list_outcomes()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(outcomes),
                    "outcomes": [
                        {
                            "id": o.id,
                            "source_id": o.source_id,
                            "target_prediction_id": o.target_prediction_id,
                            "observation_id": o.observation_id,
                            "actual_values": o.actual_values,
                            "is_ground_truth": o.is_ground_truth,
                            "authority": o.authority,
                            "metadata": o.metadata,
                        }
                        for o in outcomes
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/feedback":
            feedbacks = self.epistemic_bridge.adaptive_learning.list_feedback()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(feedbacks),
                    "feedback": [
                        {
                            "id": f.id,
                            "prediction_id": f.prediction_id,
                            "outcome_id": f.outcome_id,
                            "model_id": f.model_id,
                            "model_version": f.model_version,
                            "provider_id": f.provider_id,
                            "loss_or_error": f.loss_or_error,
                            "metrics": f.metrics,
                            "feedback_type": f.feedback_type,
                            "payload": f.payload,
                            "authority": f.authority,
                        }
                        for f in feedbacks
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/candidates":
            candidates = self.epistemic_bridge.adaptive_learning.list_candidates()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(candidates),
                    "candidates": [
                        {
                            "id": c.id,
                            "candidate_model_id": c.candidate_model_id,
                            "candidate_model_version": c.candidate_model_version,
                            "parent_model_id": c.parent_model_id,
                            "parent_model_version": c.parent_model_version,
                            "provider_id": c.provider_id,
                            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                            "parameter_fingerprint": c.parameter_fingerprint,
                            "creation_seed": c.creation_seed,
                            "learning_event_ids": c.learning_event_ids,
                            "is_deterministic": c.is_deterministic,
                            "authority": c.authority,
                        }
                        for c in candidates
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/proposals":
            proposals = self.epistemic_bridge.adaptive_learning.list_proposals()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(proposals),
                    "proposals": [
                        {
                            "id": p.id,
                            "parent_model_id": p.parent_model_id,
                            "parent_model_version": p.parent_model_version,
                            "candidate_model_id": p.candidate_model_id,
                            "candidate_model_version": p.candidate_model_version,
                            "provider_id": p.provider_id,
                            "dataset_id": p.dataset_id,
                            "baseline_metrics": p.baseline_metrics,
                            "candidate_metrics": p.candidate_metrics,
                            "metric_deltas": p.metric_deltas,
                            "drift_context": p.drift_context,
                            "rationale": p.rationale,
                            "recommendation": p.recommendation,
                            "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                            "authority": p.authority,
                        }
                        for p in proposals
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/decisions":
            decisions = self.epistemic_bridge.adaptive_learning.list_decisions()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(decisions),
                    "decisions": [
                        {
                            "id": d.id,
                            "proposal_id": d.proposal_id,
                            "candidate_model_id": d.candidate_model_id,
                            "candidate_model_version": d.candidate_model_version,
                            "decision": d.decision,
                            "decider_id": d.decider_id,
                            "decider_authority": d.decider_authority,
                            "rationale": d.rationale,
                            "cognitia_authority": d.cognitia_authority,
                        }
                        for d in decisions
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/domains":
            domains = self.epistemic_bridge.adaptive_learning.list_domains()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(domains),
                    "domains": [
                        {
                            "id": d.id,
                            "domain_id": d.domain_id,
                            "domain_version": d.domain_version,
                            "description": d.description,
                            "representation_version": d.representation_version,
                            "declared_providers": d.declared_providers,
                            "metadata": d.metadata,
                        }
                        for d in domains
                    ],
                },
            )
            return

        elif path == "/v1/learning/transfer/proposals":
            t_proposals = self.epistemic_bridge.adaptive_learning.list_transfer_proposals()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(t_proposals),
                    "proposals": [
                        {
                            "id": p.id,
                            "source_domain_id": p.source_domain_id,
                            "target_domain_id": p.target_domain_id,
                            "transfer_type": p.transfer_type.value if hasattr(p.transfer_type, "value") else str(p.transfer_type),
                            "knowledge_type": p.knowledge_type.value if hasattr(p.knowledge_type, "value") else str(p.knowledge_type),
                            "source_model_id": p.source_model_id,
                            "source_model_version": p.source_model_version,
                            "target_model_id": p.target_model_id,
                            "target_base_model_version": p.target_base_model_version,
                            "rationale": p.rationale,
                            "authority": p.authority,
                            "metadata": p.metadata,
                        }
                        for p in t_proposals
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/transfer/decisions":
            t_decisions = self.epistemic_bridge.adaptive_learning.list_transfer_decisions()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(t_decisions),
                    "decisions": [
                        {
                            "id": d.id,
                            "proposal_id": d.proposal_id,
                            "decision": d.decision,
                            "decider_id": d.decider_id,
                            "decision_source": d.decision_source,
                            "rationale": d.rationale,
                            "cognitia_authority": d.cognitia_authority,
                            "metadata": d.metadata,
                        }
                        for d in t_decisions
                    ],
                    "authority": "NONE",
                },
            )
        elif path == "/v1/learning/lifecycle/events":
            events = self.epistemic_bridge.adaptive_learning.list_lifecycle_events()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(events),
                    "events": [
                        {
                            "id": e.id,
                            "domain_id": e.domain_id,
                            "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
                            "model_id": e.model_id,
                            "model_version": e.model_version,
                            "previous_state": e.previous_state.value if hasattr(e.previous_state, "value") else str(e.previous_state),
                            "new_state": e.new_state.value if hasattr(e.new_state, "value") else str(e.new_state),
                            "actor_id": e.actor_id,
                            "decision_reference": e.decision_reference,
                            "payload": e.payload,
                            "authority": e.authority,
                            "timestamp": e.timestamp,
                        }
                        for e in events
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/rollback/proposals":
            r_props = self.epistemic_bridge.adaptive_learning.list_rollback_proposals()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(r_props),
                    "proposals": [
                        {
                            "id": p.id,
                            "domain_id": p.domain_id,
                            "current_active_model_id": p.current_active_model_id,
                            "current_active_model_version": p.current_active_model_version,
                            "target_model_id": p.target_model_id,
                            "target_model_version": p.target_model_version,
                            "reason": p.reason,
                            "risk_assessment": p.risk_assessment,
                            "factual_comparison": p.factual_comparison,
                            "authority": p.authority,
                        }
                        for p in r_props
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/rollback/decisions":
            r_decs = self.epistemic_bridge.adaptive_learning.list_rollback_decisions()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(r_decs),
                    "decisions": [
                        {
                            "id": d.id,
                            "proposal_id": d.proposal_id,
                            "domain_id": d.domain_id,
                            "target_model_id": d.target_model_id,
                            "target_model_version": d.target_model_version,
                            "approved": d.approved,
                            "decision_source": d.decision_source,
                            "decider_id": d.decider_id,
                            "decider_authority": d.decider_authority,
                            "rationale": d.rationale,
                            "cognitia_authority": d.cognitia_authority,
                        }
                        for d in r_decs
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/learning/activations":
            acts = self.epistemic_bridge.adaptive_learning.list_activation_observations()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "count": len(acts),
                    "activations": [
                        {
                            "id": a.id,
                            "domain_id": a.domain_id,
                            "model_id": a.model_id,
                            "model_version": a.model_version,
                            "task_type": a.task_type.value if hasattr(a.task_type, "value") else str(a.task_type),
                            "model_role": a.model_role,
                            "activation_type": a.activation_type,
                            "external_actor_id": a.external_actor_id,
                            "decision_reference_id": a.decision_reference_id,
                            "authority": a.authority,
                        }
                        for a in acts
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif (path.startswith("/v1/learning/models/") and path.endswith("/lineage")) or path == "/v1/learning/models/lineage":
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(self.path).query)
            if path == "/v1/learning/models/lineage":
                m_id = query.get("model_id", ["laya_acoustic_v1"])[0]
                m_ver = query.get("model_version", ["1.0.0"])[0]
                d_id = query.get("domain_id", ["default"])[0]
            else:
                parts = path.split("/")
                model_spec = parts[4]
                m_id = model_spec.split(":")[0]
                m_ver = model_spec.split(":")[1] if ":" in model_spec else query.get("model_version", ["1.0.0"])[0]
                d_id = query.get("domain_id", ["default"])[0]

            lineage = self.epistemic_bridge.adaptive_learning.reconstruct_model_lineage(
                model_id=m_id,
                model_version=m_ver,
                domain_id=d_id,
            )
            self._send_json(HTTPStatus.OK, lineage)
            return

        elif path.startswith("/v1/learning/models/") and path.endswith("/lifecycle"):
            parts = path.split("/")
            model_spec = parts[4]
            m_id = model_spec.split(":")[0]
            m_events = self.epistemic_bridge.adaptive_learning.list_lifecycle_events(model_id=m_id)
            self._send_json(
                HTTPStatus.OK,
                {
                    "model_id": m_id,
                    "lifecycle_events": [
                        {
                            "id": e.id,
                            "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
                            "model_version": e.model_version,
                            "previous_state": e.previous_state.value if hasattr(e.previous_state, "value") else str(e.previous_state),
                            "new_state": e.new_state.value if hasattr(e.new_state, "value") else str(e.new_state),
                            "actor_id": e.actor_id,
                            "payload": e.payload,
                            "timestamp": e.timestamp,
                        }
                        for e in m_events
                    ],
                    "authority": "NONE",
                },
            )
            return

        elif path == "/v1/providers":
            providers = self.provider_registry.list_providers()
            self._send_json(HTTPStatus.OK, {"providers": providers})

        else:
            self._send_error(
                HTTPStatus.NOT_FOUND, "EndpointNotFound", f"Endpoint '{self.path}' not found"
            )

    def do_POST(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        correlation_id = self.headers.get("X-Correlation-Id", str(uuid.uuid4()))

        # Content length check
        content_length_str = self.headers.get("Content-Length")
        if not content_length_str:
            self._send_error(
                HTTPStatus.LENGTH_REQUIRED,
                "LengthRequired",
                "Content-Length header required",
                correlation_id,
            )
            return

        try:
            content_length = int(content_length_str)
        except ValueError:
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                "InvalidContentLength",
                "Invalid Content-Length header",
                correlation_id,
            )
            return

        if content_length > MAX_BODY_SIZE:
            self._send_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "PayloadTooLarge",
                f"Payload exceeds limit of {MAX_BODY_SIZE} bytes",
                correlation_id,
            )
            return

        body_bytes = self.rfile.read(content_length)
        try:
            body = json.loads(body_bytes.decode("utf-8"))
        except Exception as e:
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                "InvalidJSON",
                f"Malformed JSON payload: {e}",
                correlation_id,
            )
            return

        if path == "/v1/observations":
            self.handle_post_observation(body, correlation_id)
        elif path == "/v1/evidence":
            self.handle_post_evidence(body, correlation_id)
        elif path == "/v1/directional-specifications":
            self.handle_post_directional_spec(body, correlation_id)
        elif path == "/v1/learning/predict":
            try:
                validated = ABIValidator.validate_learning_predict_dict(body)
                from cognitia.learning.representation import RepresentationAdapter
                from cognitia.learning.contract import TaskType

                model_id = validated.get("model_id", "laya_acoustic_v1")
                task_str = validated.get("task", "classification")
                task_type = TaskType(task_str)
                payload = validated.get("payload", {})
                params = validated.get("parameters", {})
                is_det = validated.get("is_deterministic", True)

                rep = RepresentationAdapter.adapt_raw(payload, source_id=f"api_predict_{uuid.uuid4().hex[:8]}")
                result = self.epistemic_bridge.adaptive_learning.infer(
                    model_id=model_id,
                    provider_id="laya",
                    task=task_type,
                    representation=rep,
                    parameters=params,
                    is_deterministic=is_det,
                )

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "inferred",
                        "id": result.id,
                        "model_id": result.model_id,
                        "model_version": result.model_version,
                        "provider_id": result.provider_id,
                        "task": result.task.value if hasattr(result.task, "value") else str(result.task),
                        "output": result.output,
                        "confidence": result.confidence,
                        "is_deterministic": result.is_deterministic,
                        "epistemic_status": result.epistemic_status,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "LEARNING_PREDICT_ERROR", str(exc))
            return

        elif path == "/v1/learning/evaluate":
            try:
                validated = ABIValidator.validate_learning_evaluate_dict(body)
                from cognitia.learning.representation import RepresentationAdapter
                from cognitia.learning.contract import TaskType

                model_id = validated.get("model_id", "laya_acoustic_v1")
                task_str = validated.get("task", "classification")
                task_type = TaskType(task_str)
                raw_dataset = validated.get("dataset", [])

                adapted_dataset = []
                for sample in raw_dataset:
                    rep = RepresentationAdapter.adapt_raw(sample.get("payload", {}), source_id=sample.get("id", "sample"))
                    adapted_dataset.append({
                        "representation": rep,
                        "expected": sample.get("expected"),
                    })

                provider = self.epistemic_bridge.adaptive_learning.get_provider("laya")
                from cognitia.learning.evaluation import ModelEvaluationEngine
                metrics = ModelEvaluationEngine.evaluate_model_on_dataset(
                    provider=provider,
                    model_id=model_id,
                    model_version="1.0.0",
                    dataset=adapted_dataset,
                    task=task_type,
                )

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "evaluated",
                        "model_id": model_id,
                        "metrics": metrics,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "LEARNING_EVALUATION_ERROR", str(exc))
            return

        elif path == "/v1/learning/compare":
            try:
                validated = ABIValidator.validate_learning_compare_dict(body)
                from cognitia.learning.representation import RepresentationAdapter
                from cognitia.learning.contract import TaskType

                models = validated.get("models", [])
                raw_dataset = validated.get("dataset", [])
                dataset_id = validated.get("dataset_id", "eval_dataset_v1")

                adapted_dataset = []
                for sample in raw_dataset:
                    rep = RepresentationAdapter.adapt_raw(sample.get("payload", {}), source_id=sample.get("id", "sample"))
                    adapted_dataset.append({
                        "representation": rep,
                        "expected": sample.get("expected"),
                    })

                comparison = self.epistemic_bridge.adaptive_learning.compare_candidate_models(
                    candidate_models=[tuple(m) for m in models],
                    dataset=adapted_dataset,
                    dataset_id=dataset_id,
                )

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "compared",
                        "id": comparison.id,
                        "dataset_id": comparison.dataset_id,
                        "candidate_models": comparison.candidate_models,
                        "metrics_by_model": comparison.metrics_by_model,
                        "advisory_summary": comparison.advisory_summary,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "LEARNING_COMPARE_ERROR", str(exc))
            return

        elif path == "/v1/learning/outcomes":
            try:
                from cognitia.learning.contract import OutcomeRecord
                source_id = body.get("source_id", "external_host")
                target_pred = body.get("target_prediction_id", "")
                obs_id = body.get("observation_id", "")
                actual_vals = body.get("actual_values", {})
                meta = body.get("metadata", {})

                outcome = OutcomeRecord(
                    source_id=source_id,
                    target_prediction_id=target_pred,
                    observation_id=obs_id,
                    actual_values=actual_vals,
                    is_ground_truth=True,
                    authority="NONE",
                    metadata=meta,
                )
                rec = self.epistemic_bridge.adaptive_learning.record_outcome(outcome)
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "recorded",
                        "id": rec.id,
                        "source_id": rec.source_id,
                        "target_prediction_id": rec.target_prediction_id,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "OUTCOME_RECORD_ERROR", str(exc))
            return

        elif path == "/v1/learning/feedback":
            try:
                prediction_id = body.get("prediction_id", "")
                outcome_id = body.get("outcome_id", "")
                outcome = self.epistemic_bridge.adaptive_learning._outcomes.get(outcome_id)
                if not outcome and "actual_values" in body:
                    from cognitia.learning.contract import OutcomeRecord
                    outcome = OutcomeRecord(
                        source_id=body.get("source_id", "external_host"),
                        target_prediction_id=prediction_id,
                        actual_values=body.get("actual_values", {}),
                        authority="NONE",
                    )
                    self.epistemic_bridge.adaptive_learning.record_outcome(outcome)

                if not outcome:
                    from cognitia.learning.contract import OutcomeRecord
                    outcome = OutcomeRecord(
                        source_id=body.get("source_id", "external_host"),
                        target_prediction_id=prediction_id,
                        actual_values=body.get("payload", {}),
                        authority="NONE",
                    )
                    self.epistemic_bridge.adaptive_learning.record_outcome(outcome)

                fb = self.epistemic_bridge.adaptive_learning.create_feedback_from_outcome(
                    prediction_id=prediction_id,
                    outcome=outcome,
                    feedback_type=body.get("feedback_type", "direct_outcome"),
                    custom_metrics=body.get("metrics"),
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "recorded",
                        "id": fb.id,
                        "prediction_id": fb.prediction_id,
                        "outcome_id": fb.outcome_id,
                        "loss_or_error": fb.loss_or_error,
                        "metrics": fb.metrics,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "FEEDBACK_RECORD_ERROR", str(exc))
            return

        elif path == "/v1/learning/update" or path == "/v1/learning/learn":
            try:
                feedback_ids = body.get("feedback_ids", [])
                base_model_id = body.get("base_model_id", "laya_acoustic_v1")
                seed = int(body.get("seed", 42))
                config = body.get("config", {})

                candidate, update, event = self.epistemic_bridge.adaptive_learning.learn_from_feedback(
                    feedback_ids=feedback_ids,
                    base_model_id=base_model_id,
                    seed=seed,
                    config=config,
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "candidate_generated",
                        "candidate_model_id": candidate.candidate_model_id,
                        "candidate_model_version": candidate.candidate_model_version,
                        "parent_model_id": candidate.parent_model_id,
                        "parent_model_version": candidate.parent_model_version,
                        "parameter_fingerprint": candidate.parameter_fingerprint,
                        "learning_event_id": event.id,
                        "learning_update_id": update.id,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "LEARNING_UPDATE_ERROR", str(exc))
            return

        elif path == "/v1/learning/promotion-proposal":
            try:
                candidate_version = body.get("candidate_version", "")
                base_version = body.get("baseline_model_version", "1.0.0")
                model_id = body.get("model_id", "laya_acoustic_v1")
                raw_dataset = body.get("dataset", [])
                dataset_id = body.get("dataset_id", "eval_dataset_v1")

                from cognitia.learning.representation import RepresentationAdapter
                adapted_dataset = []
                for sample in raw_dataset:
                    rep = RepresentationAdapter.adapt_raw(sample.get("payload", {}), source_id=sample.get("id", "sample"))
                    adapted_dataset.append({
                        "representation": rep,
                        "expected": sample.get("expected"),
                    })

                proposal = self.epistemic_bridge.adaptive_learning.create_promotion_proposal(
                    candidate_version=candidate_version,
                    baseline_model_version=base_version,
                    model_id=model_id,
                    dataset=adapted_dataset,
                    dataset_id=dataset_id,
                    drift_context=body.get("drift_context"),
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "proposal_generated",
                        "id": proposal.id,
                        "candidate_model_id": proposal.candidate_model_id,
                        "candidate_model_version": proposal.candidate_model_version,
                        "parent_model_id": proposal.parent_model_id,
                        "parent_model_version": proposal.parent_model_version,
                        "baseline_metrics": proposal.baseline_metrics,
                        "candidate_metrics": proposal.candidate_metrics,
                        "metric_deltas": proposal.metric_deltas,
                        "rationale": proposal.rationale,
                        "recommendation": proposal.recommendation,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "PROMOTION_PROPOSAL_ERROR", str(exc))
            return

        elif path == "/v1/learning/decision":
            try:
                proposal_id = body.get("proposal_id", "")
                decision = body.get("decision", "REJECTED")
                decider_id = body.get("decider_id", "external_reviewer")
                decider_auth = body.get("decider_authority", "domain_governance")
                rationale = body.get("rationale", "")

                dec_rec = self.epistemic_bridge.adaptive_learning.record_promotion_decision(
                    proposal_id=proposal_id,
                    decision=decision,
                    decider_id=decider_id,
                    decider_authority=decider_auth,
                    rationale=rationale,
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "decision_recorded",
                        "id": dec_rec.id,
                        "proposal_id": dec_rec.proposal_id,
                        "decision": dec_rec.decision,
                        "decider_id": dec_rec.decider_id,
                        "cognitia_authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "DECISION_RECORD_ERROR", str(exc))
            return

        elif path == "/v1/learning/replay":
            try:
                candidate_version = body.get("candidate_version", "")
                model_id = body.get("model_id", "laya_acoustic_v1")
                seed = int(body.get("seed", 42))

                res = self.epistemic_bridge.adaptive_learning.replay_learning(
                    candidate_version=candidate_version,
                    model_id=model_id,
                    seed=seed,
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": res.status,
                        "is_replayable": res.is_replayable,
                        "is_exact_match": res.is_exact_match,
                        "original_fingerprint": res.original_fingerprint,
                        "replayed_fingerprint": res.replayed_fingerprint,
                        "parameter_parity": res.parameter_parity,
                        "reason": res.reason,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "LEARNING_REPLAY_ERROR", str(exc))
            return

        elif path == "/v1/learning/domains":
            try:
                ABIValidator.validate_domain_dict(body)
                from cognitia.learning.contract import LearningDomain

                domain = LearningDomain(
                    domain_id=body["domain_id"],
                    domain_version=body.get("domain_version", "1.0.0"),
                    description=body.get("description", ""),
                    representation_version=body.get("representation_version", "1.0.0"),
                    declared_providers=body.get("declared_providers", ["laya"]),
                    metadata=body.get("metadata", {}),
                )
                registered = self.epistemic_bridge.adaptive_learning.register_domain(domain)
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "domain_registered",
                        "domain_id": registered.domain_id,
                        "domain_version": registered.domain_version,
                        "description": registered.description,
                        "representation_version": registered.representation_version,
                        "declared_providers": registered.declared_providers,
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "DOMAIN_REGISTRATION_ERROR", str(exc))
            return

        elif path == "/v1/learning/transfer/proposals":
            try:
                ABIValidator.validate_transfer_proposal_dict(body)
                from cognitia.learning.contract import KnowledgeType, TransferType

                proposal = self.epistemic_bridge.adaptive_learning.create_transfer_proposal(
                    source_domain_id=body["source_domain_id"],
                    target_domain_id=body["target_domain_id"],
                    source_model_id=body["source_model_id"],
                    source_model_version=body.get("source_model_version", "1.0.0"),
                    target_model_id=body.get("target_model_id", body["source_model_id"]),
                    target_base_model_version=body.get("target_base_model_version", "1.0.0"),
                    transfer_type=TransferType(body.get("transfer_type", "model_transfer")),
                    knowledge_type=KnowledgeType(body.get("knowledge_type", "feature_extractor")),
                    rationale=body.get("rationale", ""),
                    transfer_payload=body.get("transfer_payload", {}),
                    metadata=body.get("metadata", {}),
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "transfer_proposal_created",
                        "id": proposal.id,
                        "source_domain_id": proposal.source_domain_id,
                        "target_domain_id": proposal.target_domain_id,
                        "transfer_type": proposal.transfer_type.value,
                        "knowledge_type": proposal.knowledge_type.value,
                        "rationale": proposal.rationale,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "TRANSFER_PROPOSAL_ERROR", str(exc))
            return

        elif path == "/v1/learning/transfer/evaluate":
            try:
                proposal_id = body.get("proposal_id")
                if proposal_id:
                    proposal = self.epistemic_bridge.adaptive_learning._transfer_proposals.get(proposal_id)
                    if not proposal:
                        self._send_error(HTTPStatus.NOT_FOUND, "PROPOSAL_NOT_FOUND", f"Proposal '{proposal_id}' not found")
                        return
                    result = self.epistemic_bridge.adaptive_learning.evaluate_transfer_compatibility(proposal)
                else:
                    ABIValidator.validate_transfer_proposal_dict(body)
                    from cognitia.learning.contract import KnowledgeType, LearningTransferProposal, TransferType
                    temp_prop = LearningTransferProposal(
                        source_domain_id=body["source_domain_id"],
                        target_domain_id=body["target_domain_id"],
                        source_model_id=body["source_model_id"],
                        source_model_version=body.get("source_model_version", "1.0.0"),
                        target_model_id=body.get("target_model_id", body["source_model_id"]),
                        target_base_model_version=body.get("target_base_model_version", "1.0.0"),
                        transfer_type=TransferType(body.get("transfer_type", "model_transfer")),
                        knowledge_type=KnowledgeType(body.get("knowledge_type", "feature_extractor")),
                        rationale=body.get("rationale", ""),
                        transfer_payload=body.get("transfer_payload", {}),
                    )
                    result = self.epistemic_bridge.adaptive_learning.evaluate_transfer_compatibility(temp_prop)

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "compatibility_evaluated",
                        "id": result.id,
                        "compatibility_status": result.status.value,
                        "score": result.score,
                        "compatibility_details": result.compatibility_details,
                        "risks": result.risks,
                        "advisory_recommendation": result.advisory_recommendation,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "TRANSFER_EVALUATION_ERROR", str(exc))
            return

        elif path == "/v1/learning/transfer/instantiate-candidate":
            try:
                proposal_id = body.get("proposal_id", "")
                if not proposal_id:
                    self._send_error(HTTPStatus.BAD_REQUEST, "MISSING_FIELD", "Field 'proposal_id' is required")
                    return

                candidate = self.epistemic_bridge.adaptive_learning.instantiate_transfer_candidate(
                    proposal_id=proposal_id,
                    target_candidate_version=body.get("target_candidate_version"),
                    seed=int(body.get("seed", 42)),
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "target_candidate_instantiated",
                        "candidate_model_id": candidate.candidate_model_id,
                        "candidate_model_version": candidate.candidate_model_version,
                        "domain_id": candidate.domain_id,
                        "parent_model_id": candidate.parent_model_id,
                        "parent_model_version": candidate.parent_model_version,
                        "parameter_fingerprint": candidate.parameter_fingerprint,
                        "authority": "NONE",
                        "message": "Candidate created in target domain. Active model remains untouched.",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "TRANSFER_INSTANTIATION_ERROR", str(exc))
            return

        elif path == "/v1/learning/transfer/decision":
            try:
                ABIValidator.validate_transfer_decision_dict(body)
                rec = self.epistemic_bridge.adaptive_learning.record_transfer_decision(
                    proposal_id=body["proposal_id"],
                    decision=body["decision"],
                    decider_id=body.get("decider_id", "external_governance"),
                    rationale=body.get("rationale", ""),
                    metadata=body.get("metadata", {}),
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "transfer_decision_recorded",
                        "id": rec.id,
                        "proposal_id": rec.proposal_id,
                        "decision": rec.decision,
                        "decider_id": rec.decider_id,
                        "decision_source": rec.decision_source,
                        "cognitia_authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "TRANSFER_DECISION_ERROR", str(exc))
            return

        elif path in ("/v1/learning/promotion-decision", "/v1/learning/promotion/decision"):
            try:
                proposal_id = body.get("proposal_id", "")
                decision = body.get("decision", "REJECTED")
                decider_id = body.get("decider_id", "external_reviewer")
                decider_auth = body.get("decider_authority", "domain_governance")
                rationale = body.get("rationale", "")

                dec_rec = self.epistemic_bridge.adaptive_learning.record_promotion_decision(
                    proposal_id=proposal_id,
                    decision=decision,
                    decider_id=decider_id,
                    decider_authority=decider_auth,
                    rationale=rationale,
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "decision_recorded",
                        "id": dec_rec.id,
                        "proposal_id": dec_rec.proposal_id,
                        "decision": dec_rec.decision,
                        "decider_id": dec_rec.decider_id,
                        "cognitia_authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "DECISION_RECORD_ERROR", str(exc))
            return

        elif path in ("/v1/learning/rollback-proposal", "/v1/learning/rollback/proposal", "/v1/learning/rollback/propose"):
            try:
                target_model_id = body.get("target_model_id") or body.get("model_id", "laya_acoustic_v1")
                target_model_ver = body.get("target_model_version") or body.get("target_version") or body.get("model_version", "1.0.0")
                curr_active_id = body.get("current_active_model_id") or body.get("current_model_id")
                reason = body.get("reason", "")
                domain_id = body.get("domain_id", "default")
                from cognitia.learning.contract import TaskType
                task_str = body.get("task_type", "classification")
                task_type = TaskType(task_str)
                model_role = body.get("model_role", "primary")

                prop = self.epistemic_bridge.adaptive_learning.propose_model_rollback(
                    target_model_id=target_model_id,
                    target_model_version=target_model_ver,
                    current_active_model_id=curr_active_id,
                    reason=reason,
                    risk_assessment=body.get("risk_assessment"),
                    factual_comparison=body.get("factual_comparison"),
                    domain_id=domain_id,
                    task_type=task_type,
                    model_role=model_role,
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "rollback_proposed",
                        "id": prop.id,
                        "domain_id": prop.domain_id,
                        "current_active_model_id": prop.current_active_model_id,
                        "current_active_model_version": prop.current_active_model_version,
                        "target_model_id": prop.target_model_id,
                        "target_model_version": prop.target_model_version,
                        "reason": prop.reason,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "ROLLBACK_PROPOSAL_ERROR", str(exc))
            return

        elif path in ("/v1/learning/rollback-decision", "/v1/learning/rollback/decision", "/v1/learning/rollback/record-decision"):
            try:
                proposal_id = body.get("proposal_id", "")
                approved = bool(body.get("approved", False) or body.get("decision", "").upper() in ("APPROVED", "ACCEPTED"))
                decider_id = body.get("decider_id", "external_governance")
                rationale = body.get("rationale", "")
                decider_auth = body.get("decider_authority", "domain_governance_board")

                dec_rec = self.epistemic_bridge.adaptive_learning.record_rollback_decision(
                    proposal_id=proposal_id,
                    approved=approved,
                    decider_id=decider_id,
                    rationale=rationale,
                    decider_authority=decider_auth,
                    metadata=body.get("metadata"),
                )
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "rollback_decision_recorded",
                        "id": dec_rec.id,
                        "proposal_id": dec_rec.proposal_id,
                        "approved": dec_rec.approved,
                        "decision": "APPROVED" if dec_rec.approved else "REJECTED",
                        "decision_source": dec_rec.decision_source,
                        "decider_id": dec_rec.decider_id,
                        "cognitia_authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "ROLLBACK_DECISION_ERROR", str(exc))
            return

        elif path in ("/v1/learning/activation-observation", "/v1/learning/activation/observation", "/v1/learning/activations/record-observation", "/v1/learning/activations"):
            try:
                from cognitia.learning.contract import ModelActivationObservation, TaskType
                domain_id = body.get("domain_id", "default")
                model_id = body.get("model_id", "laya_acoustic_v1")
                model_version = body.get("model_version", "1.0.0")
                task_str = body.get("task_type", "classification")
                task_type = TaskType(task_str)
                model_role = body.get("model_role", "primary")
                activation_type = body.get("activation_type", "PROMOTION")
                external_actor_id = body.get("external_actor_id", "domain_operator")
                decision_ref = body.get("decision_reference_id", "")

                obs = ModelActivationObservation(
                    domain_id=domain_id,
                    model_id=model_id,
                    model_version=model_version,
                    task_type=task_type,
                    model_role=model_role,
                    activation_type=activation_type,
                    external_actor_id=external_actor_id,
                    decision_reference_id=decision_ref,
                    authority="NONE",
                )
                recorded = self.epistemic_bridge.adaptive_learning.record_activation_observation(obs)
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "activation_observed_and_reconciled",
                        "id": recorded.id,
                        "domain_id": recorded.domain_id,
                        "model_id": recorded.model_id,
                        "model_version": recorded.model_version,
                        "activation_type": recorded.activation_type,
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "ACTIVATION_OBSERVATION_ERROR", str(exc))
            return

        elif path in ("/v1/learning/freeze", "/v1/learning/domains/freeze") or (path.startswith("/v1/learning/domains/") and path.endswith("/freeze")):
            try:
                domain_id = body.get("domain_id")
                if not domain_id and path.startswith("/v1/learning/domains/"):
                    domain_id = path.split("/")[4]
                domain_id = domain_id or "default"
                from cognitia.learning.contract import DomainFreezeMode
                mode_str = body.get("mode", "frozen").lower()
                mode = DomainFreezeMode.OBSERVATION_ONLY if mode_str == "observation_only" else DomainFreezeMode.FROZEN

                res_mode = self.epistemic_bridge.adaptive_learning.freeze_domain(domain_id, mode=mode)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "domain_frozen",
                        "domain_id": domain_id,
                        "freeze_mode": res_mode.value.upper() if hasattr(res_mode, "value") else str(res_mode).upper(),
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "FREEZE_ERROR", str(exc))
            return

        elif path in ("/v1/learning/unfreeze", "/v1/learning/domains/unfreeze") or (path.startswith("/v1/learning/domains/") and path.endswith("/unfreeze")):
            try:
                domain_id = body.get("domain_id")
                if not domain_id and path.startswith("/v1/learning/domains/"):
                    domain_id = path.split("/")[4]
                domain_id = domain_id or "default"

                res_mode = self.epistemic_bridge.adaptive_learning.unfreeze_domain(domain_id)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "domain_unfrozen",
                        "domain_id": domain_id,
                        "freeze_mode": res_mode.value.upper() if hasattr(res_mode, "value") else str(res_mode).upper(),
                        "authority": "NONE",
                    },
                )
            except Exception as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "UNFREEZE_ERROR", str(exc))
            return

        elif path in (
            "/v1/learning/transfer/activate",
            "/v1/transfer/activate",
            "/v1/learning/activate",
            "/v1/learning/models/activate",
            "/v1/learning/models/promote-active",
            "/v1/learning/models/rollback-active",
            "/v1/models/activate",
        ):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                "ACTIVATION_FORBIDDEN",
                "Activation is an external domain authority operation and cannot be controlled or executed by Cognitia.",
                correlation_id,
            )
            return
        elif path == "/v1/providers/register":
            self._send_error(
                HTTPStatus.FORBIDDEN,
                "DynamicRegistrationDisabled",
                "Dynamic provider registration is disabled in local-first runtime",
                correlation_id,
            )
        else:
            self._send_error(
                HTTPStatus.NOT_FOUND, "EndpointNotFound", f"Endpoint '{self.path}' not found"
            )

    def _extract_and_validate_provider(
        self, body: dict[str, Any], default_cap: str, correlation_id: str
    ) -> tuple[str, str] | None:
        provider_id = (
            self.headers.get("X-Cognitia-Provider-Id")
            or body.get("source_id")
            or body.get("producer_id")
            or body.get("provider_id")
        )
        capability = (
            self.headers.get("X-Cognitia-Capability")
            or body.get("metadata", {}).get("capability", default_cap)
        )

        if not provider_id:
            self._send_error(
                HTTPStatus.UNAUTHORIZED,
                "MissingProviderIdentification",
                "Missing provider identification in X-Cognitia-Provider-Id header or payload",
                correlation_id,
            )
            return None

        if not self.provider_registry.is_registered(provider_id):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                "UnregisteredProvider",
                f"Provider '{provider_id}' is not in Cognitia static whitelist",
                correlation_id,
            )
            return None

        if not self.provider_registry.validate_capability(provider_id, capability):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                "UnauthorizedCapability",
                f"Provider '{provider_id}' is not authorized for capability '{capability}'",
                correlation_id,
            )
            return None

        if not self.rate_limiter.check_rate_limit(provider_id):
            self._send_error(
                HTTPStatus.TOO_MANY_REQUESTS,
                "RateLimitExceeded",
                f"Rate limit exceeded for provider '{provider_id}'",
                correlation_id,
            )
            return None

        return str(provider_id), str(capability)

    def handle_post_observation(self, body: dict[str, Any], correlation_id: str) -> None:
        t_start = time.perf_counter()

        prov_info = self._extract_and_validate_provider(
            body, default_cap="observe.generic", correlation_id=correlation_id
        )
        if not prov_info:
            return
        provider_id, capability = prov_info

        # ABI Validation
        try:
            ABIValidator.validate_observation_dict(body)
        except (ABIValidationError, RuntimeValidationError) as e:
            self._send_error(
                HTTPStatus.BAD_REQUEST, "ABIValidationError", str(e), correlation_id
            )
            return

        # Security Sanitization
        try:
            sanitized_payload = SecuritySanitizer.sanitize_observation_payload(
                body.get("payload", {}), provider_id
            )
            body["payload"] = sanitized_payload
        except SecurityValidationError as e:
            self._send_error(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "SecurityViolation",
                str(e),
                correlation_id,
            )
            return

        # Epistemic Ingestion & Durable Persistence
        try:
            ingest_result = self.epistemic_bridge.ingest_observation(
                body, provider_id, capability
            )
            duration_ms = (time.perf_counter() - t_start) * 1000.0

            response_payload = {
                "status": "success",
                "correlation_id": correlation_id,
                "provider_id": provider_id,
                "capability": capability,
                "processing_duration_ms": round(duration_ms, 3),
                "ingest_result": ingest_result,
            }
            self._send_json(HTTPStatus.OK, response_payload)
        except EpistemicCapacityExceededError as e:
            self._send_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "CapacityExceeded",
                str(e),
                correlation_id,
            )
        except PersistenceWriteError as e:
            logger.error(f"Persistence write failure during observation ingestion: {e}")
            self._send_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "PersistenceFailure",
                f"Durable storage write failed: {e}",
                correlation_id,
            )
        except PersistenceError as e:
            logger.error(f"Persistence error: {e}")
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "PersistenceError",
                f"Persistence failure: {e}",
                correlation_id,
            )
        except Exception:
            logger.exception("Unexpected error ingesting observation")
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "IngestionError",
                "Internal epistemic ingestion failed",
                correlation_id,
            )

    def handle_post_evidence(self, body: dict[str, Any], correlation_id: str) -> None:
        t_start = time.perf_counter()

        prov_info = self._extract_and_validate_provider(
            body, default_cap="observe.evidence", correlation_id=correlation_id
        )
        if not prov_info:
            return
        provider_id, capability = prov_info

        # Evidence Validation
        try:
            ABIValidator.validate_evidence_dict(body)
        except (ABIValidationError, RuntimeValidationError) as e:
            self._send_error(
                HTTPStatus.BAD_REQUEST, "EvidenceValidationError", str(e), correlation_id
            )
            return

        # Epistemic Ingestion & Durable Persistence
        try:
            ingest_result = self.epistemic_bridge.ingest_evidence(
                body, provider_id, capability
            )
            duration_ms = (time.perf_counter() - t_start) * 1000.0

            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "provider_id": provider_id,
                    "capability": capability,
                    "processing_duration_ms": round(duration_ms, 3),
                    "ingest_result": ingest_result,
                },
            )
        except EpistemicCapacityExceededError as e:
            self._send_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "CapacityExceeded",
                str(e),
                correlation_id,
            )
        except PersistenceWriteError as e:
            logger.error(f"Persistence write failure during evidence ingestion: {e}")
            self._send_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "PersistenceFailure",
                f"Durable storage write failed: {e}",
                correlation_id,
            )
        except PersistenceError as e:
            logger.error(f"Persistence error: {e}")
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "PersistenceError",
                f"Persistence failure: {e}",
                correlation_id,
            )
        except Exception:
            logger.exception("Unexpected error ingesting evidence")
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "IngestionError",
                "Internal evidence ingestion failed",
                correlation_id,
            )

    def handle_post_directional_spec(
        self, body: dict[str, Any], correlation_id: str
    ) -> None:
        prov_info = self._extract_and_validate_provider(
            body, default_cap="propose.directional", correlation_id=correlation_id
        )
        if not prov_info:
            return
        provider_id, _ = prov_info

        try:
            ABIValidator.validate_directional_spec_dict(body)
        except (ABIValidationError, RuntimeValidationError) as e:
            self._send_error(
                HTTPStatus.BAD_REQUEST, "SpecificationValidationError", str(e), correlation_id
            )
            return

        try:
            proposal = self.epistemic_bridge.ingest_directional_specification(
                body, provider_id
            )
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "proposal": proposal,
                },
            )
        except PersistenceWriteError as e:
            logger.error(f"Persistence write failure during directional proposal: {e}")
            self._send_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "PersistenceFailure",
                f"Durable storage write failed: {e}",
                correlation_id,
            )
        except PersistenceError as e:
            logger.error(f"Persistence error: {e}")
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "PersistenceError",
                f"Persistence failure: {e}",
                correlation_id,
            )
        except Exception:
            logger.exception("Unexpected error evaluating directional specification")
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "EvaluationError",
                "Directional specification evaluation failed",
                correlation_id,
            )


def create_gateway_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    config_dir: Path | None = None,
    persistence_service: FilePersistenceService | None = None,
) -> ThreadingHTTPServer:
    """Factory to create and configure the Cognitia Gateway HTTP Server with Persistence."""
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent.parent / "config"

    whitelist_path = config_dir / "provider_whitelist.json"
    registry = ProviderRegistry(whitelist_path if whitelist_path.exists() else None)
    limiter = RateLimiter(max_requests_per_minute=600)

    # Initialize Persistence if not explicitly passed
    if persistence_service is None:
        config_path = config_dir / "runtime_config.json"
        pers_config: dict[str, Any] = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg_json = json.load(f)
                    pers_config = cfg_json.get("persistence", {})
            except Exception as e:
                logger.warning(f"Could not load runtime_config.json: {e}")

        pers_enabled = pers_config.get("enabled", True)
        ephemeral_mode = (
            os.environ.get("COGNITIA_EPHEMERAL_MODE", "").lower() in ("true", "1")
            or pers_config.get("ephemeral_mode", False)
        )
        data_dir_env = os.environ.get("COGNITIA_DATA_DIR")
        if data_dir_env:
            data_dir = Path(data_dir_env)
        else:
            configured_dir = pers_config.get("data_dir", "/var/lib/cognitia/epistemic")
            if configured_dir.startswith("/var/") and os.name == "nt":
                data_dir = Path(__file__).resolve().parent.parent / "data" / "epistemic"
            else:
                data_dir = Path(configured_dir)

        durability_str = pers_config.get("durability", "sync")
        durability = (
            DurabilityMode.SYNC
            if durability_str == "sync"
            else (
                DurabilityMode.ASYNC
                if durability_str == "async"
                else DurabilityMode.NONE
            )
        )
        snapshot_interval = int(pers_config.get("snapshot_interval_records", 1000))
        max_journal_bytes = int(pers_config.get("journal_max_bytes", 268435456))

        if pers_enabled:
            persistence_service = FilePersistenceService(
                data_dir=data_dir,
                durability_mode=durability,
                snapshot_interval_records=snapshot_interval,
                max_journal_bytes=max_journal_bytes,
                ephemeral_mode=ephemeral_mode,
            )

    bridge = EpistemicBridge(persistence_service=persistence_service)

    # Safely close previous handler bridge persistence if present
    if hasattr(CognitiaGatewayHandler, "epistemic_bridge") and CognitiaGatewayHandler.epistemic_bridge:
        old_pers = getattr(CognitiaGatewayHandler.epistemic_bridge, "persistence_service", None)
        if old_pers and hasattr(old_pers, "close"):
            try:
                old_pers.close()
            except Exception:
                pass

    # Bind handlers
    CognitiaGatewayHandler.provider_registry = registry
    CognitiaGatewayHandler.rate_limiter = limiter
    CognitiaGatewayHandler.epistemic_bridge = bridge

    server = ThreadingHTTPServer((host, port), CognitiaGatewayHandler)
    return server
