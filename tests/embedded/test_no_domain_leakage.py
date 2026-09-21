"""Phase 5A: Domain Neutrality Tests."""

from __future__ import annotations

import ast
import pathlib

import pytest


class TestNoDomainLeakage:
    """Cognitia core contains no references to host-specific domain vocabulary."""

    FORBIDDEN_TERMS = [
        "Frappe",
        "Oracle",
        "SalesOrder",
        "PurchaseOrder",
        "Invoice",
        "Customer",
        "ERP",
        "Django",
        "FastAPI",
        "PostgreSQL",
        "REST",
        "HTTP",
    ]

    @pytest.fixture
    def core_source_files(self) -> list[pathlib.Path]:
        src_dir = pathlib.Path(__file__).resolve().parents[3] / "src" / "cognitia"
        return list(src_dir.rglob("*.py"))

    def test_no_forbidden_domain_terms(self, core_source_files: list[pathlib.Path]) -> None:
        violations = []
        for file_path in core_source_files:
            text = file_path.read_text(encoding="utf-8")
            for term in self.FORBIDDEN_TERMS:
                if term in text:
                    violations.append((file_path, term))
        assert violations == [], f"Forbidden domain terms found in core: {violations}"
