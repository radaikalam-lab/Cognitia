"""Tests for Runtime HTTP Gateway AL1 Endpoints: Outcomes, Feedback, Update, Proposals, Decisions, Replay."""

import json
from http import HTTPStatus
from pathlib import Path
import threading
import time
import unittest
import urllib.request

from runtime.gateway.app import create_gateway_server, CognitiaGatewayHandler


class TestRuntimeAL1GatewayEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8993
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

    def test_01_predict_outcome_and_feedback_flow(self):
        # 1. Prediction
        predict_payload = {
            "model_id": "laya_acoustic_v1",
            "task": "classification",
            "payload": {"spl_db": 91.0, "frequency_hz": 1100.0},
        }
        req_pred = urllib.request.Request(
            f"{self.base_url}/v1/learning/predict",
            data=json.dumps(predict_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_pred) as resp:
            self.assertEqual(resp.status, 200)
            pred_data = json.loads(resp.read().decode("utf-8"))
            pred_id = pred_data["id"]
            self.assertEqual(pred_data["authority"], "NONE")

        # 2. Record Outcome
        outcome_payload = {
            "source_id": "test_mic",
            "target_prediction_id": pred_id,
            "actual_values": {"label": "harmonic"},
        }
        req_out = urllib.request.Request(
            f"{self.base_url}/v1/learning/outcomes",
            data=json.dumps(outcome_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_out) as resp:
            self.assertEqual(resp.status, 201)
            out_data = json.loads(resp.read().decode("utf-8"))
            outcome_id = out_data["id"]
            self.assertEqual(out_data["authority"], "NONE")

        # 3. Record Feedback
        feedback_payload = {
            "prediction_id": pred_id,
            "outcome_id": outcome_id,
            "feedback_type": "direct_outcome",
        }
        req_fb = urllib.request.Request(
            f"{self.base_url}/v1/learning/feedback",
            data=json.dumps(feedback_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_fb) as resp:
            self.assertEqual(resp.status, 201)
            fb_data = json.loads(resp.read().decode("utf-8"))
            fb_id = fb_data["id"]
            self.assertEqual(fb_data["authority"], "NONE")

        # 4. Trigger Learning Update / Candidate generation
        update_payload = {
            "feedback_ids": [fb_id],
            "base_model_id": "laya_acoustic_v1",
            "seed": 42,
        }
        req_update = urllib.request.Request(
            f"{self.base_url}/v1/learning/update",
            data=json.dumps(update_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_update) as resp:
            self.assertEqual(resp.status, 200)
            update_data = json.loads(resp.read().decode("utf-8"))
            cand_ver = update_data["candidate_model_version"]
            self.assertEqual(update_data["authority"], "NONE")
            self.assertIn("candidate", cand_ver)

        # 5. Generate Promotion Proposal
        proposal_payload = {
            "candidate_version": cand_ver,
            "baseline_model_version": "1.0.0",
            "model_id": "laya_acoustic_v1",
            "dataset": [
                {"payload": {"spl_db": 91.0}, "expected": "harmonic"},
            ],
        }
        req_prop = urllib.request.Request(
            f"{self.base_url}/v1/learning/promotion-proposal",
            data=json.dumps(proposal_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_prop) as resp:
            self.assertEqual(resp.status, 200)
            prop_data = json.loads(resp.read().decode("utf-8"))
            prop_id = prop_data["id"]
            self.assertEqual(prop_data["authority"], "NONE")

        # 6. Record External Governance Decision
        decision_payload = {
            "proposal_id": prop_id,
            "decision": "ACCEPTED",
            "decider_id": "api_test_reviewer",
            "decider_authority": "Governance Test Board",
        }
        req_dec = urllib.request.Request(
            f"{self.base_url}/v1/learning/decision",
            data=json.dumps(decision_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_dec) as resp:
            self.assertEqual(resp.status, 201)
            dec_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(dec_data["cognitia_authority"], "NONE")
            self.assertEqual(dec_data["decision"], "ACCEPTED")

        # 7. Replay Verification Endpoint
        replay_payload = {
            "candidate_version": cand_ver,
            "model_id": "laya_acoustic_v1",
            "seed": 42,
        }
        req_rep = urllib.request.Request(
            f"{self.base_url}/v1/learning/replay",
            data=json.dumps(replay_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_rep) as resp:
            self.assertEqual(resp.status, 200)
            rep_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(rep_data["authority"], "NONE")
            self.assertEqual(rep_data["status"], "VERIFIED")
            self.assertTrue(rep_data["is_exact_match"])

        # 8. Query GET endpoints
        for endpoint in ["outcomes", "feedback", "candidates", "proposals", "decisions"]:
            req_get = urllib.request.urlopen(f"{self.base_url}/v1/learning/{endpoint}")
            self.assertEqual(req_get.status, 200)
            get_data = json.loads(req_get.read().decode("utf-8"))
            self.assertEqual(get_data["authority"], "NONE")
            self.assertGreaterEqual(get_data["count"], 1)
