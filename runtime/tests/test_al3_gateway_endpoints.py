"""Tests for Runtime HTTP Gateway AL3 Endpoints:
Lifecycle Events, Lineage, Rollback Proposals/Decisions, Activation Observations, Domain Freeze, and Activation Guard.
"""

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


class TestRuntimeAL3GatewayEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8996
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

    def test_01_models_listing_and_lifecycle_state(self):
        req = urllib.request.Request(f"{self.base_url}/v1/learning/models?domain_id=default", method="GET")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("models", data)
            self.assertGreater(len(data["models"]), 0)
            model = data["models"][0]
            self.assertIn("lifecycle_state", model)
            self.assertIn("runtime_activation_state", model)
            self.assertIn("task_type", model)
            self.assertIn("model_role", model)

    def test_02_model_rollback_and_governance_flow(self):
        # 1. Propose rollback (authority=NONE)
        prop_payload = {
            "model_id": "laya_acoustic_v1",
            "current_version": "1.0.0",
            "target_version": "1.0.0",
            "reason": "Performance degradation observed in production canary",
            "domain_id": "default",
        }
        req = urllib.request.Request(
            f"{self.base_url}/v1/learning/rollback/propose",
            data=json.dumps(prop_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 201)
            proposal = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(proposal["authority"], "NONE")
            self.assertEqual(proposal["status"], "rollback_proposed")
            prop_id = proposal["id"]

        # 2. Record rollback external decision
        dec_payload = {
            "proposal_id": prop_id,
            "decision": "APPROVED",
            "decider_id": "lead_governance_operator",
            "decider_authority": "cluster_ops",
            "rationale": "Safety rollback verified by team",
        }
        req_dec = urllib.request.Request(
            f"{self.base_url}/v1/learning/rollback/record-decision",
            data=json.dumps(dec_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_dec) as resp:
            self.assertEqual(resp.status, 201)
            dec_rec = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(dec_rec["decision_source"], "EXTERNAL")
            self.assertEqual(dec_rec["cognitia_authority"], "NONE")
            self.assertEqual(dec_rec["decision"], "APPROVED")

        # 3. Query rollback proposals
        req_list = urllib.request.Request(f"{self.base_url}/v1/learning/rollback/proposals?domain_id=default", method="GET")
        with urllib.request.urlopen(req_list) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreater(len(data["proposals"]), 0)

    def test_03_activation_observation_and_lineage(self):
        # 1. Record activation observation from external domain runtime
        obs_payload = {
            "domain_id": "default",
            "model_id": "laya_acoustic_v1",
            "model_version": "1.0.0",
            "activation_type": "PROMOTION",
            "external_actor_id": "k8s_model_operator",
            "authority": "NONE",
        }
        req_obs = urllib.request.Request(
            f"{self.base_url}/v1/learning/activations/record-observation",
            data=json.dumps(obs_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_obs) as resp:
            self.assertEqual(resp.status, 201)
            obs = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(obs["authority"], "NONE")
            self.assertEqual(obs["model_version"], "1.0.0")

        # 2. Query activation history
        req_act_hist = urllib.request.Request(f"{self.base_url}/v1/learning/activations?domain_id=default", method="GET")
        with urllib.request.urlopen(req_act_hist) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreater(len(data["activations"]), 0)

        # 3. Query model lineage
        req_lin = urllib.request.Request(f"{self.base_url}/v1/learning/models/lineage?model_id=laya_acoustic_v1&model_version=1.0.0&domain_id=default", method="GET")
        with urllib.request.urlopen(req_lin) as resp:
            self.assertEqual(resp.status, 200)
            lineage = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(lineage["model_id"], "laya_acoustic_v1")
            self.assertEqual(lineage["model_version"], "1.0.0")

    def test_04_domain_freeze_and_unfreeze_flow(self):
        # Freeze domain
        freeze_payload = {"domain_id": "default", "mode": "OBSERVATION_ONLY", "reason": "Canary observation period"}
        req_fr = urllib.request.Request(
            f"{self.base_url}/v1/learning/domains/freeze",
            data=json.dumps(freeze_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_fr) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res["freeze_mode"], "OBSERVATION_ONLY")

        # Unfreeze domain
        unfreeze_payload = {"domain_id": "default"}
        req_unfr = urllib.request.Request(
            f"{self.base_url}/v1/learning/domains/unfreeze",
            data=json.dumps(unfreeze_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_unfr) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res["freeze_mode"], "NORMAL")

    def test_05_autonomous_activation_strictly_forbidden(self):
        endpoints = [
            "/v1/learning/models/activate",
            "/v1/learning/models/promote-active",
            "/v1/learning/models/rollback-active",
            "/v1/learning/activate",
        ]
        for ep in endpoints:
            req = urllib.request.Request(
                f"{self.base_url}{ep}",
                data=json.dumps({"model_id": "laya_acoustic_v1", "model_version": "1.0.0"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 403)
            err_data = json.loads(ctx.exception.read().decode("utf-8"))
            self.assertEqual(err_data["error_code"], "ACTIVATION_FORBIDDEN")
            self.assertEqual(err_data["authority"], "NONE")
