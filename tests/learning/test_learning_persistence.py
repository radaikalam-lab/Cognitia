"""Tests for Adaptive Learning Service and Persistence Recovery."""

import tempfile
from pathlib import Path

from cognitia.abi.types import Observation
from cognitia.learning.contract import TaskType
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import ModelRecord, ModelStatus
from runtime.persistence.file_persistence import FilePersistenceService


def test_service_inference_and_persistence_recovery():
    """Verify that predictions, learning curves, and models persist across restarts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # 1. Initialize Persistence and Service
        pers = FilePersistenceService(data_dir=data_dir)
        pers.initialize_and_recover()
        service = AdaptiveLearningService(persistence_service=pers)

        # Register model
        m_rec = ModelRecord(
            model_id="laya_acoustic_v1",
            model_version="1.0.0",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
        service.register_model(m_rec)

        # Perform inference
        obs = Observation(source_id="mic_01", payload={"spl_db": 90.0})
        res = service.predict_from_observation(obs, model_id="laya_acoustic_v1")
        assert res.authority == "NONE"
        assert len(service.list_history()) == 1

        # Record learning curve point
        service.record_learning_point(
            model_id="laya_acoustic_v1",
            model_version="1.0.0",
            provider_id="laya",
            step=1,
            sample_count=100,
            metrics={"accuracy": 0.85},
        )

        # Check drift
        service.check_drift(
            model_id="laya_acoustic_v1",
            baseline_distribution={"resonance": 0.8, "noise": 0.2},
            current_distribution={"resonance": 0.2, "noise": 0.8},
        )

        pers.close()

        # 2. Restart and recover
        pers2 = FilePersistenceService(data_dir=data_dir)

        from runtime.gateway.epistemic_bridge import EpistemicBridge
        bridge = EpistemicBridge(persistence_service=pers2)

        try:
            assert len(bridge.adaptive_learning.list_history()) == 1
            recovered_res = bridge.adaptive_learning.list_history()[0]
            assert recovered_res.id == res.id
            assert recovered_res.authority == "NONE"
            assert len(bridge.adaptive_learning.list_learning_curves()) == 1
            assert len(bridge.adaptive_learning.list_drift_reports()) == 1
        finally:
            pers2.close()
