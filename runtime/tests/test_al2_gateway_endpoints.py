"""Tests for Runtime HTTP Gateway AL2 Endpoints: Domains, Transfer Proposals, Compatibility, Instantiation, Decision, and Activation Guard."""

import json
from http import HTTPStatus
from pathlib import Path
import threading
import time
import unittest
import urllib.request
import urllib.error

import tempfile

from runtime.gateway.app import create_gateway_server, CognitiaGatewayHandler
from runtime.persistence.file_persistence import FilePersistenceService


class TestRuntimeAL2GatewayEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8994
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.data_dir = Path(cls.temp_dir.name)
        cls.pers = FilePersistenceService(data_dir=cls.data_dir)
        config_dir = Path("E:/Cognitia/runtime/config")
        cls.server = create_gateway_server(
            host="127.0.0.1",
            port=cls.port,
            config_dir=config_dir,
            persistence_service=cls.pers,
        )
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        if hasattr(CognitiaGatewayHandler, "epistemic_bridge") and CognitiaGatewayHandler.epistemic_bridge:
            pers = CognitiaGatewayHandler.epistemic_bridge.persistence_service
            if pers and hasattr(pers, "close"):
                pers.close()
        cls.temp_dir.cleanup()


    def test_01_domain_registration_and_listing(self):
        # 1. Register domain Alpha
        payload_alpha = {
            "domain_id": "gateway_alpha",
            "domain_version": "1.0.0",
            "description": "Gateway Alpha domain",
            "representation_version": "1.0.0",
            "declared_providers": ["laya"],
        }
        req = urllib.request.Request(
            f"{self.base_url}/v1/learning/domains",
            data=json.dumps(payload_alpha).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["domain_id"], "gateway_alpha")

        # 2. Register domain Beta
        payload_beta = {
            "domain_id": "gateway_beta",
            "domain_version": "1.0.0",
            "description": "Gateway Beta domain",
            "representation_version": "1.0.0",
            "declared_providers": ["laya"],
        }
        req_b = urllib.request.Request(
            f"{self.base_url}/v1/learning/domains",
            data=json.dumps(payload_beta).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_b) as resp:
            self.assertEqual(resp.status, 201)

        # 3. List domains
        req_list = urllib.request.Request(f"{self.base_url}/v1/learning/domains", method="GET")
        with urllib.request.urlopen(req_list) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            d_ids = [d["domain_id"] for d in data["domains"]]
            self.assertIn("default", d_ids)
            self.assertIn("gateway_alpha", d_ids)
            self.assertIn("gateway_beta", d_ids)

    def test_02_transfer_proposal_and_compatibility_flow(self):
        # 1. Create Transfer Proposal
        prop_payload = {
            "source_domain_id": "gateway_alpha",
            "target_domain_id": "gateway_beta",
            "source_model_id": "alpha_model",
            "source_model_version": "1.0.0",
            "target_model_id": "beta_model",
            "transfer_type": "feature_extractor_transfer",
            "knowledge_type": "feature_extractor",
            "rationale": "Transfer gateway alpha feature representation",
            "transfer_payload": {"layers": ["conv1", "conv2"]},
        }
        req_prop = urllib.request.Request(
            f"{self.base_url}/v1/learning/transfer/proposals",
            data=json.dumps(prop_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_prop) as resp:
            self.assertEqual(resp.status, 201)
            prop_data = json.loads(resp.read().decode("utf-8"))
            prop_id = prop_data["id"]
            self.assertEqual(prop_data["authority"], "NONE")

        # 2. Evaluate Transfer Compatibility
        eval_payload = {"proposal_id": prop_id}
        req_eval = urllib.request.Request(
            f"{self.base_url}/v1/learning/transfer/evaluate",
            data=json.dumps(eval_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_eval) as resp:
            self.assertEqual(resp.status, 200)
            eval_data = json.loads(resp.read().decode("utf-8"))
            self.assertIn(eval_data["compatibility_status"], ["compatible", "partially_compatible"])
            self.assertEqual(eval_data["authority"], "NONE")

        # 3. Instantiate Candidate in Target Domain
        inst_payload = {
            "proposal_id": prop_id,
            "target_candidate_version": "1.1-gateway-candidate",
            "seed": 42,
        }
        req_inst = urllib.request.Request(
            f"{self.base_url}/v1/learning/transfer/instantiate-candidate",
            data=json.dumps(inst_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_inst) as resp:
            self.assertEqual(resp.status, 201)
            inst_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(inst_data["candidate_model_version"], "1.1-gateway-candidate")
            self.assertEqual(inst_data["domain_id"], "gateway_beta")
            self.assertEqual(inst_data["authority"], "NONE")

        # 4. Record External Transfer Decision
        dec_payload = {
            "proposal_id": prop_id,
            "decision": "ACCEPTED",
            "decider_id": "gateway_admin_user",
            "rationale": "Verified through simulation",
        }
        req_dec = urllib.request.Request(
            f"{self.base_url}/v1/learning/transfer/decision",
            data=json.dumps(dec_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_dec) as resp:
            self.assertEqual(resp.status, 201)
            dec_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(dec_data["decision"], "ACCEPTED")
            self.assertEqual(dec_data["decision_source"], "EXTERNAL")
            self.assertEqual(dec_data["cognitia_authority"], "NONE")

        # 5. List Decisions
        req_list_dec = urllib.request.Request(f"{self.base_url}/v1/learning/transfer/decisions", method="GET")
        with urllib.request.urlopen(req_list_dec) as resp:
            self.assertEqual(resp.status, 200)
            list_data = json.loads(resp.read().decode("utf-8"))
            self.assertGreaterEqual(list_data["count"], 1)

    def test_03_activation_endpoint_is_forbidden(self):
        """Negative Gateway Test: Ensure activation endpoint fails with 403 Forbidden."""
        req_act = urllib.request.Request(
            f"{self.base_url}/v1/learning/transfer/activate",
            data=json.dumps({"model_id": "test_model"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req_act)
        self.assertEqual(ctx.exception.code, 403)
