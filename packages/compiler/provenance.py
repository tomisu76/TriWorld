"""Provenance tracking: source manifest, evidence ledger, build metadata.

Tracks all input sources, their licenses, hashes, and processing steps
for full reproducibility and auditability.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from packages.contracts.map_request import MapCompilationRequest


@dataclass
class SourceEntry:
    """A single source data entry in the provenance ledger."""

    source_id: str
    kind: str  # "osm", "dem", "imagery", "synthetic"
    provider: str
    url: str
    license: str
    sha256: str
    bytes: int
    fetched_at: str  # ISO 8601 UTC
    bounds: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    crs: Optional[str] = None
    vertical_datum: Optional[str] = None
    resolution: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingStep:
    """A processing step in the pipeline."""

    step_id: str
    name: str
    started_at: str  # ISO 8601 UTC
    completed_at: str  # ISO 8601 UTC
    duration_ms: int
    input_refs: List[str]  # source_ids or step_ids
    output_refs: List[str]  # artifact paths
    status: str  # "passed", "failed", "skipped"
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class BuildManifest:
    """Complete build manifest with provenance."""

    build_id: str
    compiler_version: str
    request_hash: str
    request: Dict[str, Any]
    sources: List[SourceEntry]
    steps: List[ProcessingStep]
    created_at: str  # ISO 8601 UTC
    tool_versions: Dict[str, str]
    source_licenses: List[str]
    projection: Dict[str, Any]
    seed: int
    validation_report: str
    output_sha256: Optional[str] = None
    output_bytes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "buildId": self.build_id,
            "compilerVersion": self.compiler_version,
            "requestHash": self.request_hash,
            "request": self.request,
            "sources": [s.__dict__ for s in self.sources],
            "steps": [s.__dict__ for s in self.steps],
            "createdAt": self.created_at,
            "toolVersions": self.tool_versions,
            "sourceLicenses": self.source_licenses,
            "projection": self.projection,
            "seed": self.seed,
            "validationReport": self.validation_report,
            "outputSha256": self.output_sha256,
            "outputBytes": self.output_bytes,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


class ProvenanceLedger:
    """Tracks provenance for a build."""

    def __init__(
        self,
        request: MapCompilationRequest,
        compiler_version: str = "0.1.0",
        tool_versions: Optional[Dict[str, str]] = None,
    ):
        self.request = request
        self.request_hash = self._compute_request_hash(request)
        self.compiler_version = compiler_version
        self.build_id = hashlib.sha256(
            f"{self.request_hash}:{time.time()}".encode()
        ).hexdigest()[:16]
        self.sources: List[SourceEntry] = []
        self.steps: List[ProcessingStep] = []
        self.tool_versions = tool_versions or {}
        self.source_licenses: List[str] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self._active_steps: Dict[str, ProcessingStep] = {}

    def _compute_request_hash(self, request: MapCompilationRequest) -> str:
        """Compute a deterministic hash of the request."""
        request_dict = request.model_dump(mode="json")
        return hashlib.sha256(
            json.dumps(request_dict, sort_keys=True).encode()
        ).hexdigest()

    def add_source(self, entry: SourceEntry) -> None:
        """Add a source entry to the ledger."""
        self.sources.append(entry)
        if entry.license not in self.source_licenses:
            self.source_licenses.append(entry.license)

    def begin_step(
        self,
        step_id: str,
        name: str,
        input_refs: List[str],
    ) -> str:
        """Begin a processing step."""
        now = datetime.now(timezone.utc).isoformat()
        step = ProcessingStep(
            step_id=step_id,
            name=name,
            started_at=now,
            completed_at=now,
            duration_ms=0,
            input_refs=input_refs,
            output_refs=[],
            status="running",
        )
        self._active_steps[step_id] = step
        return step_id

    def complete_step(
        self,
        step_id: str,
        output_refs: List[str],
        status: str = "passed",
        metrics: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
    ) -> None:
        """Complete a processing step."""
        if step_id not in self._active_steps:
            raise ValueError(f"Step {step_id} not started")

        step = self._active_steps.pop(step_id)
        now = datetime.now(timezone.utc).isoformat()
        start_dt = datetime.fromisoformat(step.started_at)
        end_dt = datetime.fromisoformat(now)
        duration_ms = int((end_dt - start_dt).total_seconds() * 1000)

        step.completed_at = now
        step.duration_ms = duration_ms
        step.output_refs = output_refs
        step.status = status
        if metrics:
            step.metrics.update(metrics)
        if warnings:
            step.warnings.extend(warnings)

        self.steps.append(step)

    def get_source(self, source_id: str) -> Optional[SourceEntry]:
        """Look up a source by ID."""
        for s in self.sources:
            if s.source_id == source_id:
                return s
        return None

    def get_step(self, step_id: str) -> Optional[ProcessingStep]:
        """Look up a step by ID."""
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def to_manifest(
        self,
        projection: Dict[str, Any],
        validation_report: str,
        output_sha256: Optional[str] = None,
        output_bytes: Optional[int] = None,
    ) -> BuildManifest:
        """Generate a complete BuildManifest."""
        return BuildManifest(
            build_id=self.build_id,
            compiler_version=self.compiler_version,
            request_hash=self.request_hash,
            request=self.request.model_dump(mode="json"),
            sources=self.sources,
            steps=self.steps,
            created_at=self.created_at,
            tool_versions=self.tool_versions,
            source_licenses=self.source_licenses,
            projection=projection,
            seed=self.request.seed,
            validation_report=validation_report,
            output_sha256=output_sha256,
            output_bytes=output_bytes,
        )

    def save_manifest(
        self,
        path: Path,
        projection: Dict[str, Any],
        validation_report: str,
        output_sha256: Optional[str] = None,
        output_bytes: Optional[int] = None,
    ) -> None:
        """Save the build manifest to a file."""
        manifest = self.to_manifest(
            projection, validation_report, output_sha256, output_bytes
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manifest.to_json(indent=2))
