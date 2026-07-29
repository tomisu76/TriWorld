"""Tests for provenance tracking: source manifest, evidence ledger."""

import json
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime

import pytest

from packages.compiler.provenance import (
    SourceEntry,
    ProcessingStep,
    BuildManifest,
    ProvenanceLedger,
)
from packages.contracts.map_request import MapCompilationRequest


def make_request():
    """Create a valid MapCompilationRequest for testing."""
    return MapCompilationRequest(
        name="test_level",
        center={"lat": 48.85, "lon": 2.35},
        extent={"widthM": 2000.0, "heightM": 2000.0},
        terrainResolutionM=2.0,
        seed=42,
    )


class TestSourceEntry:
    def test_source_entry_creation(self):
        """Test SourceEntry creation."""
        entry = SourceEntry(
            source_id="osm-overpass-1",
            kind="osm",
            provider="overpass-api.de",
            url="https://overpass-api.de/api/interpreter",
            license="ODbL-1.0",
            sha256="abc123",
            bytes=1024,
            fetched_at="2024-01-01T00:00:00Z",
            bounds=[2.34, 48.84, 2.36, 48.86],
        )
        assert entry.source_id == "osm-overpass-1"
        assert entry.kind == "osm"
        assert entry.license == "ODbL-1.0"
        assert entry.bounds == [2.34, 48.84, 2.36, 48.86]

    def test_source_entry_optional_fields(self):
        """Test SourceEntry with optional fields."""
        entry = SourceEntry(
            source_id="dem-1",
            kind="dem",
            provider="mapzen",
            url="https://tile.nextzen.org",
            license="CC0-1.0",
            sha256="def456",
            bytes=2048,
            fetched_at="2024-01-01T00:00:00Z",
        )
        assert entry.bounds is None
        assert entry.crs is None
        assert entry.metadata == {}


class TestProcessingStep:
    def test_processing_step_creation(self):
        """Test ProcessingStep creation."""
        step = ProcessingStep(
            step_id="osm-fetch-1",
            name="fetch_osm",
            started_at="2024-01-01T00:00:00Z",
            completed_at="2024-01-01T00:00:01Z",
            duration_ms=1000,
            input_refs=[],
            output_refs=["cache/osm/abc.osm"],
            status="passed",
        )
        assert step.step_id == "osm-fetch-1"
        assert step.status == "passed"
        assert step.output_refs == ["cache/osm/abc.osm"]


class TestBuildManifest:
    def test_build_manifest_creation(self):
        """Test BuildManifest creation."""
        manifest = BuildManifest(
            build_id="build-001",
            compiler_version="0.1.0",
            request_hash="abc123",
            request={},
            sources=[],
            steps=[],
            created_at="2024-01-01T00:00:00Z",
            tool_versions={"python": "3.12"},
            source_licenses=["ODbL-1.0"],
            projection={"crs": "EPSG:4326"},
            seed=42,
            validation_report="structural_validation: passed",
        )
        assert manifest.build_id == "build-001"
        assert manifest.sources == []
        assert manifest.steps == []

    def test_build_manifest_to_dict(self):
        """Test BuildManifest serialization."""
        source = SourceEntry(
            source_id="osm-1",
            kind="osm",
            provider="overpass",
            url="https://example.com",
            license="ODbL",
            sha256="abc",
            bytes=100,
            fetched_at="2024-01-01T00:00:00Z",
        )
        manifest = BuildManifest(
            build_id="build-001",
            compiler_version="0.1.0",
            request_hash="abc123",
            request={},
            sources=[source],
            steps=[],
            created_at="2024-01-01T00:00:00Z",
            tool_versions={"python": "3.12"},
            source_licenses=["ODbL"],
            projection={"crs": "EPSG:4326"},
            seed=42,
            validation_report="passed",
        )
        d = manifest.to_dict()
        assert d["buildId"] == "build-001"
        assert len(d["sources"]) == 1
        assert d["sources"][0]["source_id"] == "osm-1"

    def test_build_manifest_to_json(self):
        """Test BuildManifest JSON serialization."""
        manifest = BuildManifest(
            build_id="build-001",
            compiler_version="0.1.0",
            request_hash="abc123",
            request={},
            sources=[],
            steps=[],
            created_at="2024-01-01T00:00:00Z",
            tool_versions={},
            source_licenses=[],
            projection={},
            seed=42,
            validation_report="passed",
        )
        json_str = manifest.to_json()
        d = json.loads(json_str)
        assert d["buildId"] == "build-001"


class TestProvenanceLedger:
    def test_ledger_init(self):
        """Test ProvenanceLedger initialization."""
        request = make_request()
        ledger = ProvenanceLedger(request=request)
        assert ledger.build_id is not None
        assert len(ledger.sources) == 0
        assert len(ledger.steps) == 0

    def test_ledger_add_source(self):
        """Test adding a source entry."""
        request = make_request()
        ledger = ProvenanceLedger(request=request)
        entry = SourceEntry(
            source_id="osm-1",
            kind="osm",
            provider="overpass",
            url="https://example.com",
            license="ODbL",
            sha256="abc123",
            bytes=100,
            fetched_at="2024-01-01T00:00:00Z",
        )
        ledger.add_source(entry)
        assert len(ledger.sources) == 1
        assert ledger.sources[0].source_id == "osm-1"
        assert "ODbL" in ledger.source_licenses

    def test_ledger_begin_complete_step(self):
        """Test begin/complete step lifecycle."""
        request = make_request()
        ledger = ProvenanceLedger(request=request)
        step_id = ledger.begin_step("step-1", "fetch_osm", [])
        assert step_id == "step-1"
        ledger.complete_step("step-1", ["cache/osm/abc.osm"], status="passed")
        assert len(ledger.steps) == 1
        assert ledger.steps[0].status == "passed"

    def test_ledger_get_source(self):
        """Test source lookup."""
        request = make_request()
        ledger = ProvenanceLedger(request=request)
        entry = SourceEntry(
            source_id="osm-1",
            kind="osm",
            provider="overpass",
            url="https://example.com",
            license="ODbL",
            sha256="abc123",
            bytes=100,
            fetched_at="2024-01-01T00:00:00Z",
        )
        ledger.add_source(entry)
        found = ledger.get_source("osm-1")
        assert found is not None
        assert found.source_id == "osm-1"
        assert ledger.get_source("nonexistent") is None

    def test_ledger_get_step(self):
        """Test step lookup."""
        request = make_request()
        ledger = ProvenanceLedger(request=request)
        ledger.begin_step("step-1", "fetch_osm", [])
        ledger.complete_step("step-1", [], status="passed")
        found = ledger.get_step("step-1")
        assert found is not None
        assert found.step_id == "step-1"
        assert ledger.get_step("nonexistent") is None

    def test_ledger_to_manifest(self):
        """Test manifest generation."""
        request = make_request()
        ledger = ProvenanceLedger(request=request)
        source = SourceEntry(
            source_id="osm-1",
            kind="osm",
            provider="overpass",
            url="https://example.com",
            license="ODbL",
            sha256="abc123",
            bytes=100,
            fetched_at="2024-01-01T00:00:00Z",
        )
        ledger.add_source(source)
        ledger.begin_step("step-1", "fetch_osm", [])
        ledger.complete_step("step-1", [], status="passed")
        manifest = ledger.to_manifest(
            projection={"crs": "EPSG:32631"},
            validation_report="structural_validation: passed",
        )
        assert manifest.build_id == ledger.build_id
        assert len(manifest.sources) == 1
        assert len(manifest.steps) == 1
        assert manifest.seed == 42

    def test_ledger_save_manifest(self):
        """Test saving manifest to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            request = make_request()
            ledger = ProvenanceLedger(request=request)
            source = SourceEntry(
                source_id="osm-1",
                kind="osm",
                provider="overpass",
                url="https://example.com",
                license="ODbL",
                sha256="abc123",
                bytes=100,
                fetched_at="2024-01-01T00:00:00Z",
            )
            ledger.add_source(source)
            manifest_path = Path(tmpdir) / "manifest.json"
            ledger.save_manifest(
                manifest_path,
                projection={"crs": "EPSG:32631"},
                validation_report="passed",
            )
            assert manifest_path.exists()
            with open(manifest_path) as f:
                data = json.load(f)
            assert data["buildId"] == ledger.build_id
            assert len(data["sources"]) == 1

    def test_ledger_request_hash_deterministic(self):
        """Test that request hash is deterministic."""
        request1 = make_request()
        request2 = make_request()
        ledger1 = ProvenanceLedger(request=request1)
        ledger2 = ProvenanceLedger(request=request2)
        assert ledger1.request_hash == ledger2.request_hash
