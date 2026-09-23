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
            "message": message,
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
            models = self.epistemic_bridge.adaptive_learning.model_registry.list_versions("laya_acoustic_v1")
            active_rec = self.epistemic_bridge.adaptive_learning.model_registry.get_active("laya_acoustic_v1")
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "operational",
                    "provider": "laya",
                    "active_model": active_rec.model_id if active_rec else "laya_acoustic_v1",
                    "available_models": [
                        {
                            "model_id": m.model_id,
                            "model_version": m.model_version,
                            "provider": m.provider,
                            "is_deterministic": m.is_deterministic,
                            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                        }
                        for m in models
                    ] or [
                        {
                            "model_id": "laya_acoustic_v1",
                            "model_version": "1.0.0",
                            "provider": "laya",
                            "is_deterministic": True,
                            "status": "active",
                        }
                    ],
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
