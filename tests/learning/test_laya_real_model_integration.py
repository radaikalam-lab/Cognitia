"""Tests for Real Laya Provider Integration Boundary (AL3-A).

Verifies the real Laya provider adapter, offline local inference, model artifact
verification, checksum validation, and explicit error handling on missing models.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningResult,
    ModelInputRepresentation,
    TaskType,
)
from cognitia.learning.laya_provider import (
    LayaProviderAdapter,
    RealLayaProvider,
)
from cognitia.models.registry import ModelRecord, ModelStatus


def test_real_laya_provider_identity():
    """Verify RealLayaProvider declares provider_type as 'real'."""
    provider = RealLayaProvider()
    assert provider.provider_id == "laya_real"
    assert provider.provider_version == "1.0.0"
    assert provider.provider_type == "real"

    adapter = LayaProviderAdapter()
    assert adapter.provider_type == "real"


def test_real_laya_missing_directory_fails_explicitly():
    """Verify RealLayaProvider fails explicitly when model directory does not exist."""
    provider = RealLayaProvider(model_dir="/non/existent/laya/dir")
    rep = ModelInputRepresentation(source_reference="test_obs")
    req = AdaptiveInferenceRequest(
        model_id="laya_real_v1",
        model_version="1.0.0",
        task=TaskType.CLASSIFICATION,
        representation=rep,
    )

    with pytest.raises(AdaptiveLearningFailure) as exc_info:
        provider.infer(req)

    assert exc_info.value.error_code == "LAYA_MODEL_NOT_INSTALLED"
    assert "model directory" in str(exc_info.value).lower()


def test_real_laya_missing_artifacts_fail_explicitly():
    """Verify missing weights or config files raise specific error codes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty dir -> missing weights
        provider = RealLayaProvider(model_dir=tmpdir)
        rec = ModelRecord(model_id="laya_real_v1", model_version="1.0.0", provider="laya_real")

        with pytest.raises(AdaptiveLearningFailure) as exc_weights:
            provider.load_model(rec)
        assert exc_weights.value.error_code == "LAYA_MODEL_ARTIFACT_MISSING"

        # Add weights but missing config
        Path(tmpdir, "model.onnx").write_bytes(b"dummy_weights_content_12345")
        with pytest.raises(AdaptiveLearningFailure) as exc_config:
            provider.load_model(rec)
        assert exc_config.value.error_code == "LAYA_CONFIGURATION_INVALID"

        # Add config but missing tokenizer
        Path(tmpdir, "config.json").write_text(json.dumps({
            "model_variant": "laya-transformer-base",
            "license": "Apache-2.0",
            "upstream_repository": "https://github.com/receptron/laya",
        }))
        with pytest.raises(AdaptiveLearningFailure) as exc_tokenizer:
            provider.load_model(rec)
        assert exc_tokenizer.value.error_code == "LAYA_MODEL_ARTIFACT_MISSING"


def test_real_laya_checksum_mismatch_fails_explicitly():
    """Verify checksum mismatch raises LAYA_CHECKSUM_MISMATCH."""
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "model.onnx").write_bytes(b"weights_data_abc")
        Path(tmpdir, "config.json").write_text(json.dumps({"model_variant": "base"}))
        Path(tmpdir, "tokenizer.json").write_text(json.dumps({"vocab": []}))

        provider = RealLayaProvider(
            model_dir=tmpdir,
            expected_checksums={"weights": "expected_different_sha256_hash"},
        )
        rec = ModelRecord(model_id="laya_real_v1", model_version="1.0.0", provider="laya_real")

        with pytest.raises(AdaptiveLearningFailure) as exc:
            provider.load_model(rec)
        assert exc.value.error_code == "LAYA_CHECKSUM_MISMATCH"


def test_real_laya_valid_model_offline_inference():
    """Verify real provider successfully runs local offline inference when artifacts exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        weights_bytes = b"real_laya_onnx_weights_mock_bytes_54321"
        Path(tmpdir, "model.onnx").write_bytes(weights_bytes)
        Path(tmpdir, "config.json").write_text(json.dumps({
            "model_variant": "transformer-base",
            "license": "Apache-2.0",
            "upstream_repository": "https://github.com/receptron/laya",
            "classes": ["resonance", "harmonic", "noise", "measurement_error", "unknown"],
        }))
        Path(tmpdir, "tokenizer.json").write_text(json.dumps({"vocab": ["resonance", "noise"]}))

        provider = RealLayaProvider(model_dir=tmpdir, is_deterministic=True)
        rec = ModelRecord(model_id="laya_real_v1", model_version="1.0.0", provider="laya_real")
        provider.load_model(rec)

        rep = ModelInputRepresentation(
            source_reference="sensor_reading_101",
            features={"resonance": 1.2, "spl_db": 88.0},
            sanitized_text="Harmonic signal input",
        )
        req = AdaptiveInferenceRequest(
            model_id="laya_real_v1",
            model_version="1.0.0",
            task=TaskType.CLASSIFICATION,
            representation=rep,
        )

        res = provider.infer(req)

        assert isinstance(res, AdaptiveLearningResult)
        assert res.authority == "NONE"
        assert res.provider_id == "laya_real"
        assert res.output["model_format"] == "onnx"
        assert "decision" in res.output
        assert "scores" in res.output
        assert res.confidence > 0.0

        # Verify provenance was captured
        prov_meta = provider._model_provenance.get("laya_real_v1")
        assert prov_meta is not None
        assert prov_meta["is_real_model"] is True
        assert prov_meta["license"] == "Apache-2.0"
        assert len(prov_meta["weights_checksum"]) == 64
