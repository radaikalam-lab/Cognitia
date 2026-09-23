"""Cognitia Standalone Runtime Gateway HTTP Service.

Zero external dependencies - Uses Python Standard Library HTTP server.
Bound strictly to 127.0.0.1 (Local-First).
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

COGNITIA_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(COGNITIA_SRC) not in sys.path:
    sys.path.insert(0, str(COGNITIA_SRC))

from runtime.gateway.abi_validator import ABIValidator, ABIValidationError
from runtime.gateway.provider_registry import ProviderRegistry, ProviderRecord
from runtime.gateway.security import RateLimiter, SecuritySanitizer, SecurityValidationError
from runtime.gateway.epistemic_bridge import EpistemicBridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CognitiaRuntime] %(message)s",
)
logger = logging.getLogger("CognitiaGateway")

MAX_REQUEST_SIZE = 512 * 1024  # 512 KB


class CognitiaGatewayHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Cognitia Gateway REST API."""

    protocol_version = "HTTP/1.1"

    # Injected references
    provider_registry: ProviderRegistry
    rate_limiter: RateLimiter
    epistemic_bridge: EpistemicBridge

    def _send_json(self, status_code: int, data: dict[str, Any]) -> None:
        raw_body = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw_body)))
        self.send_header("X-Cognitia-ABI-Version", "1.0.0")
        self.send_header("X-Cognitia-Protocol-Version", "1.0.0")
        self.end_headers()
        self.wfile.write(raw_body)

    def _send_error(self, status_code: int, error_type: str, message: str, details: Any = None) -> None:
        payload = {
            "status": "error",
            "error_type": error_type,
            "message": message,
            "timestamp": time.time(),
        }
        if details:
            payload["details"] = details
        self._send_json(status_code, payload)

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path == "/v1/health":
            self.handle_health()
        elif path == "/v1/capabilities":
            self.handle_capabilities()
        elif path == "/v1/providers":
            self.handle_providers()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "NotFound", f"Endpoint '{path}' not found.")

    def do_POST(self) -> None:
        path = self.path.split("?")[0]

        # 1. Content Length Check
        content_length_str = self.headers.get("Content-Length")
        if not content_length_str:
            self._send_error(HTTPStatus.LENGTH_REQUIRED, "LengthRequired", "Missing Content-Length header")
            return

        try:
            content_length = int(content_length_str)
        except ValueError:
            self._send_error(HTTPStatus.BAD_REQUEST, "InvalidHeader", "Invalid Content-Length header")
            return

        if content_length > MAX_REQUEST_SIZE:
            self._send_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "PayloadTooLarge",
                f"Payload size {content_length} bytes exceeds 512 KB limit",
            )
            return

        # 2. Read Body
        body_bytes = self.rfile.read(content_length)
        try:
            body_json = json.loads(body_bytes.decode("utf-8"))
        except Exception as e:
            self._send_error(HTTPStatus.BAD_REQUEST, "MalformedJSON", f"Invalid JSON payload: {str(e)}")
            return

        # 3. Route POST Endpoints
        if path == "/v1/observations":
            self.handle_post_observation(body_json)
        elif path == "/v1/evidence":
            self.handle_post_evidence(body_json)
        elif path == "/v1/directional-specifications":
            self.handle_post_directional_spec(body_json)
        elif path == "/v1/providers/register":
            self.handle_register_provider(body_json)
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "NotFound", f"Endpoint '{path}' not found.")

    def handle_health(self) -> None:
        status_info = {
            "status": "healthy",
            "runtime_version": "1.0.0",
            "cognitive_abi_version": "1.0.0",
            "protocol_version": "1.0.0",
            "transport": "local_http",
            "bind_address": "127.0.0.1",
            "authority_model": "NONE",
            "epistemic": self.epistemic_bridge.get_status_summary(),
            "registered_providers_count": len(self.provider_registry.list_providers()),
        }
        self._send_json(HTTPStatus.OK, status_info)

    def handle_capabilities(self) -> None:
        providers = self.provider_registry.list_providers()
        all_caps = []
        for p in providers:
            for cap in p.get("capabilities", []):
                all_caps.append({
                    "provider_id": p["provider_id"],
                    "capability": cap,
                    "authority_level": p.get("authority_level", "NONE"),
                })
        self._send_json(HTTPStatus.OK, {"capabilities": all_caps})

    def handle_providers(self) -> None:
        providers = self.provider_registry.list_providers()
        self._send_json(HTTPStatus.OK, {"providers": providers})

    def handle_register_provider(self, body: dict[str, Any]) -> None:
        provider_id = body.get("provider_id")
        if not provider_id:
            self._send_error(HTTPStatus.BAD_REQUEST, "InvalidProvider", "Missing provider_id")
            return
        
        # Enforce authority level NONE
        record = ProviderRecord(
            provider_id=provider_id,
            provider_name=body.get("provider_name", provider_id),
            provider_version=body.get("provider_version", "1.0.0"),
            adapter_version=body.get("adapter_version", "1.0.0"),
            supported_abi_versions=body.get("supported_abi_versions", ["1.0.0"]),
            capabilities=body.get("capabilities", []),
            authority_level="NONE",  # Invariant: Never allow elevation
            transport=body.get("transport", "local_http"),
        )
        self.provider_registry.register_provider(record)
        self._send_json(HTTPStatus.CREATED, {"status": "registered", "provider_id": provider_id})

    def handle_post_observation(self, body: dict[str, Any]) -> None:
        t_start = time.time()
        correlation_id = str(uuid.uuid4())

        # 1. Extract Provider ID & Capability
        provider_id = self.headers.get("X-Cognitia-Provider-Id") or body.get("source_id") or body.get("provider_id")
        capability = self.headers.get("X-Cognitia-Capability") or body.get("metadata", {}).get("capability", "observe.generic")

        if not provider_id:
            self._send_error(HTTPStatus.UNAUTHORIZED, "UnauthorizedProvider", "Missing provider ID in headers or payload")
            return

        # 2. Provider Registration & Capability Validation
        if not self.provider_registry.is_registered(provider_id):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                "UnregisteredProvider",
                f"Provider '{provider_id}' is not registered in Cognitia Provider Registry",
            )
            return

        if not self.provider_registry.validate_capability(provider_id, capability):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                "UnauthorizedCapability",
                f"Provider '{provider_id}' is not authorized for capability '{capability}'",
            )
            return

        # 3. Rate Limit Check
        if not self.rate_limiter.check_rate_limit(provider_id):
            self._send_error(
                HTTPStatus.TOO_MANY_REQUESTS,
                "RateLimitExceeded",
                f"Rate limit exceeded for provider '{provider_id}'",
            )
            return

        # 4. ABI Validation
        try:
            ABIValidator.validate_observation_dict(body)
        except ABIValidationError as e:
            self._send_error(HTTPStatus.BAD_REQUEST, "ABIValidationError", str(e))
            return

        # 5. Security Sanitization & Isolation
        try:
            sanitized_payload = SecuritySanitizer.sanitize_observation_payload(body.get("payload", {}), provider_id)
            body["payload"] = sanitized_payload
        except SecurityValidationError as e:
            self._send_error(HTTPStatus.UNPROCESSABLE_ENTITY, "SecurityViolation", str(e))
            return

        # 6. Epistemic Ingestion
        try:
            ingest_result = self.epistemic_bridge.ingest_observation(body, provider_id, capability)
            duration_ms = (time.time() - t_start) * 1000.0
            
            response_payload = {
                "status": "success",
                "correlation_id": correlation_id,
                "provider_id": provider_id,
                "capability": capability,
                "processing_duration_ms": round(duration_ms, 3),
                "ingest_result": ingest_result,
            }
            self._send_json(HTTPStatus.OK, response_payload)
        except Exception as e:
            logger.exception("Error ingesting observation")
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "IngestError", f"Failed to ingest observation: {str(e)}")

    def handle_post_evidence(self, body: dict[str, Any]) -> None:
        self.handle_post_observation(body)

    def handle_post_directional_spec(self, body: dict[str, Any]) -> None:
        provider_id = self.headers.get("X-Cognitia-Provider-Id") or body.get("metadata", {}).get("provider_id", "anonymous")
        try:
            proposal = self.epistemic_bridge.ingest_directional_specification(body, provider_id)
            self._send_json(HTTPStatus.OK, {
                "status": "success",
                "proposal": proposal,
            })
        except Exception as e:
            self._send_error(HTTPStatus.BAD_REQUEST, "SpecificationError", str(e))


def create_gateway_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    config_dir: Path | None = None,
) -> ThreadingHTTPServer:
    """Factory to create and configure the Cognitia Gateway HTTP Server."""
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent.parent / "config"

    whitelist_path = config_dir / "provider_whitelist.json"
    registry = ProviderRegistry(whitelist_path if whitelist_path.exists() else None)
    limiter = RateLimiter(max_requests_per_minute=1200)
    bridge = EpistemicBridge()

    # Bind handlers
    CognitiaGatewayHandler.provider_registry = registry
    CognitiaGatewayHandler.rate_limiter = limiter
    CognitiaGatewayHandler.epistemic_bridge = bridge

    server = ThreadingHTTPServer((host, port), CognitiaGatewayHandler)
    return server