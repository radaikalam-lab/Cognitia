"""Tests for Runtime HTTP Gateway Adaptive Learning Endpoints."""

import json
from http import HTTPStatus
import threading
import urllib.request
from pathlib import Path
import time
import unittest

from runtime.gateway.app import create_gateway_server, CognitiaGatewayHandler


class TestRuntimeLearningGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8991
        config_dir = Path("E:/Cognitia/runtime/config")
        cls.server = create_gateway_server(host="127.0.0.1", port=cls.port, config_dir=config_dir)
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

    def test_01_capabilities_includes_adaptive_learning(self):
        req = urllib.request.urlopen(f"{self.base_url}/v1/capabilities")
        self.assertEqual(req.status, 200)
        cap_data = json.loads(req.read().decode("utf-8"))
        cap_names = [c.get("capability") or c.get("capability_id") for c in cap_data.get("capabilities", [])]
        self.assertIn("learn.adaptive", cap_names)

    def test_02_learning_models_endpoint(self):
        req_m = urllib.request.urlopen(f"{self.base_url}/v1/learning/models")
        self.assertEqual(req_m.status, 200)
        m_data = json.loads(req_m.read().decode("utf-8"))
        self.assertEqual(m_data["authority"], "NONE")
        self.assertEqual(m_data["provider"], "laya")

    def test_03_learning_predict_endpoint(self):
        predict_payload = {
            "model_id": "laya_acoustic_v1",
            "task": "classification",
            "payload": {"spl_db": 92.4, "frequency_hz": 880.0},
            "is_deterministic": True,
        }
        req_pred = urllib.request.Request(
            f"{self.base_url}/v1/learning/predict",
            data=json.dumps(predict_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_pred) as resp:
            self.assertEqual(resp.status, 200)
            res_body = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res_body["status"], "inferred")
            self.assertEqual(res_body["authority"], "NONE")
            self.assertIn("decision", res_body["output"])

    def test_04_learning_history_endpoint(self):
        req_hist = urllib.request.urlopen(f"{self.base_url}/v1/learning/history")
        self.assertEqual(req_hist.status, 200)
        h_data = json.loads(req_hist.read().decode("utf-8"))
        self.assertGreaterEqual(h_data["count"], 1)
        self.assertEqual(h_data["results"][0]["authority"], "NONE")

    def test_05_learning_evaluate_endpoint(self):
        eval_payload = {
            "model_id": "laya_acoustic_v1",
            "task": "classification",
            "dataset": [
                {"id": "s1", "payload": {"spl_db": 95.0, "frequency_hz": 440.0}, "expected": "resonance"},
                {"id": "s2", "payload": {"spl_db": 20.0, "frequency_hz": 120.0}, "expected": "noise"},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/v1/learning/evaluate",
            data=json.dumps(eval_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res["status"], "evaluated")
            self.assertEqual(res["authority"], "NONE")
            self.assertIn("accuracy", res["metrics"])

    def test_06_learning_compare_endpoint(self):
        comp_payload = {
            "models": [["laya_acoustic_v1", "1.0.0"], ["laya_acoustic_v2", "2.0.0"]],
            "dataset_id": "bench_01",
            "dataset": [
                {"id": "s1", "payload": {"spl_db": 95.0, "frequency_hz": 440.0}, "expected": "resonance"},
                {"id": "s2", "payload": {"spl_db": 20.0, "frequency_hz": 120.0}, "expected": "noise"},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/v1/learning/compare",
            data=json.dumps(comp_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res["status"], "compared")
            self.assertEqual(res["authority"], "NONE")
            self.assertIn("advisory_summary", res)
