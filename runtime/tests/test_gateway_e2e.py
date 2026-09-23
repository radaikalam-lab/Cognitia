"""End-to-End Test Suite for Cognitia Gateway Server."""

import unittest
import threading
import time
import json
import uuid
import datetime
import urllib.request
import urllib.error
from pathlib import Path
import sys

COGNITIA_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(COGNITIA_SRC) not in sys.path:
    sys.path.insert(0, str(COGNITIA_SRC))
RUNTIME_DIR = Path(__file__).resolve().parent.parent
if str(RUNTIME_DIR.parent) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR.parent))

from runtime.gateway.app import create_gateway_server


class TestGatewayE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8899
        cls.server = create_gateway_server(
            host="127.0.0.1",
            port=cls.port,
            config_dir=RUNTIME_DIR / "config",
        )
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, path: str, data: dict, headers: dict = None) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{self.port}{path}"
        body = json.dumps(data).encode("utf-8")
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return resp.status, res_data
        except urllib.error.HTTPError as e:
            res_data = json.loads(e.read().decode("utf-8"))
            return e.code, res_data

    def _get(self, path: str) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data

    def test_health_check_endpoint(self):
        status, data = self._get("/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["cognitive_abi_version"], "1.0.0")
        self.assertEqual(data["epistemic"]["status"], "available")
        self.assertEqual(data["authority_model"], "NONE")

    def test_capabilities_endpoint(self):
        status, data = self._get("/v1/capabilities")
        self.assertEqual(status, 200)
        caps = [c["capability"] for c in data["capabilities"]]
        self.assertIn("observe.navigation", caps)
        self.assertIn("observe.authorized_content", caps)

    def test_providers_endpoint(self):
        status, data = self._get("/v1/providers")
        self.assertEqual(status, 200)
        provider_ids = [p["provider_id"] for p in data["providers"]]
        self.assertIn("thorium.browser", provider_ids)
        self.assertIn("acoustiforge.adapter", provider_ids)

    def test_post_observation_authorized(self):
        obs = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "metadata": {"test": True},
            "payload": {"url": "https://example.org", "title": "Example Domain"},
        }
        headers = {
            "X-Cognitia-Provider-Id": "thorium.browser",
            "X-Cognitia-Capability": "observe.navigation",
        }
        status, data = self._post("/v1/observations", obs, headers)
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "success")
        self.assertIn("correlation_id", data)
        self.assertEqual(data["ingest_result"]["status"], "ingested")

    def test_post_directional_specification_advisory(self):
        spec = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "objectives": [{"description": "Assess browser memory usage gradient"}],
            "constraints": [{"description": "Advisory only"}],
            "success_criteria": [{"description": "Residual < 10MB"}],
        }
        headers = {
            "X-Cognitia-Provider-Id": "thorium.browser",
        }
        status, data = self._post("/v1/directional-specifications", spec, headers)
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "success")
        proposal = data["proposal"]
        self.assertEqual(proposal["status"], "advisory_candidate")
        self.assertEqual(proposal["authority"], "NONE")

    def test_post_observation_unauthorized_capability(self):
        obs = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "payload": {"cmd": "fake"},
        }
        headers = {
            "X-Cognitia-Provider-Id": "thorium.browser",
            "X-Cognitia-Capability": "execute.command",  # Forbidden capability
        }
        status, data = self._post("/v1/observations", obs, headers)
        self.assertEqual(status, 403)
        self.assertEqual(data["error_type"], "UnauthorizedCapability")

    def test_post_oversized_payload_rejection(self):
        # 600 KB payload (exceeds 512 KB limit)
        huge_text = "A" * (600 * 1024)
        obs = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "payload": {"large_data": huge_text},
        }
        headers = {
            "X-Cognitia-Provider-Id": "thorium.browser",
            "X-Cognitia-Capability": "observe.navigation",
        }
        status, data = self._post("/v1/observations", obs, headers)
        self.assertEqual(status, 413)
        self.assertEqual(data["error_type"], "PayloadTooLarge")

    def test_post_malformed_json_rejection(self):
        url = f"http://127.0.0.1:{self.port}/v1/observations"
        req = urllib.request.Request(
            url,
            data=b"INVALID_NON_JSON_DATA",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("Should have failed with HTTP 400")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)


if __name__ == "__main__":
    unittest.main()