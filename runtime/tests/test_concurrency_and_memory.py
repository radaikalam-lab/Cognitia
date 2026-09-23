"""Test Suite for Concurrency, Thread Safety, and Epistemic Memory Limits."""

import unittest
import threading
import uuid
import datetime
import time
from pathlib import Path
import sys

COGNITIA_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(COGNITIA_SRC) not in sys.path:
    sys.path.insert(0, str(COGNITIA_SRC))
RUNTIME_DIR = Path(__file__).resolve().parent.parent
if str(RUNTIME_DIR.parent) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR.parent))

from runtime.gateway.epistemic_bridge import EpistemicBridge, EpistemicCapacityExceededError
from runtime.gateway.security import RateLimiter
from cognitia.epistemic.service import InMemoryEpistemicService


class TestConcurrencyAndMemory(unittest.TestCase):
    def test_concurrent_observation_ingestion(self):
        service = InMemoryEpistemicService()
        bridge = EpistemicBridge(service)
        errors = []

        def worker(worker_id: int):
            try:
                for i in range(25):
                    obs_id = str(uuid.uuid4())
                    obs_dict = {
                        "id": obs_id,
                        "schema_version": "1.0.0",
                        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "source_id": "thorium.browser",
                        "metadata": {"thread": worker_id, "idx": i},
                        "payload": {"data": f"thread_{worker_id}_sample_{i}"},
                    }
                    res = bridge.ingest_observation(
                        obs_dict, "thorium.browser", "observe.navigation"
                    )
                    if res["status"] != "ingested":
                        errors.append(f"Unexpected status: {res}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Encountered concurrency errors: {errors}")
        self.assertEqual(len(service._nodes), 200)
        self.assertEqual(bridge._ingested_observations_count, 200)

    def test_rate_limiter_concurrency(self):
        limiter = RateLimiter(max_requests_per_minute=200)
        results = []

        def hit_limiter():
            for _ in range(30):
                r = limiter.check_rate_limit("concurrent.provider")
                results.append(r)

        threads = [threading.Thread(target=hit_limiter) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 150)
        self.assertTrue(all(results))  # All 150 requests within 200 limit succeed


if __name__ == "__main__":
    unittest.main()