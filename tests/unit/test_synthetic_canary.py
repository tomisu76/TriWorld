"""Tests for the synthetic canary BeamNG level generator."""

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import pytest

from packages.compiler.synthetic_canary import create_synthetic_canary


def test_import_create_synthetic_canary():
    """Verify that create_synthetic_canary can be imported."""
    assert callable(create_synthetic_canary)


def test_canary_zip_structure():
    """Generate a canary ZIP and verify its internal structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_zip = Path(tmpdir) / "canary.zip"
        file_hashes = create_synthetic_canary(output_zip, level_name="synthetic_canary")

        assert output_zip.exists()
        assert output_zip.stat().st_size > 0

        with zipfile.ZipFile(output_zip, 'r') as zf:
            names = zf.namelist()

            # No absolute paths
            for name in names:
                assert not name.startswith('/'), f"Absolute path found: {name}"
                assert not name.startswith('\\'), f"Backslash absolute path found: {name}"

            # No path traversal
            for name in names:
                assert '..' not in name, f"Path traversal found: {name}"

            # Every entry uses forward slashes
            for name in names:
                assert '\\' not in name, f"Backslash in path: {name}"

            # Expected levels/<level_name>/ structure
            level_prefix = "levels/synthetic_canary/"
            level_entries = [n for n in names if n.startswith(level_prefix)]
            assert len(level_entries) > 0, "No entries under levels/synthetic_canary/"

            # info.json exists
            assert f"{level_prefix}info.json" in names, "info.json missing"

            # main/items.level.json exists
            assert f"{level_prefix}main/items.level.json" in names, "main/items.level.json missing"

            # DAE exists
            dae_entries = [n for n in names if n.endswith('.dae')]
            assert len(dae_entries) > 0, "No DAE file found"

            # Terrain file exists
            ter_entries = [n for n in names if n.endswith('.ter')]
            assert len(ter_entries) > 0, "No .ter file found"

            # reports/build-manifest.json exists
            assert f"{level_prefix}reports/build-manifest.json" in names, "build-manifest.json missing"

            # reports/validation.json exists
            assert f"{level_prefix}reports/validation.json" in names, "validation.json missing"

            # Verify validation.json content
            val_data = json.loads(zf.read(f"{level_prefix}reports/validation.json"))
            assert val_data["structural_validation"] == "passed"
            assert val_data["beamng_runtime_validation"] == "not_run"

            # Verify build-manifest.json content
            manifest = json.loads(zf.read(f"{level_prefix}reports/build-manifest.json"))
            assert "files" in manifest
            assert len(manifest["files"]) > 0

            # Verify file_hashes returned match
            assert len(file_hashes) > 0


def test_canary_determinism():
    """Generate the ZIP twice and verify SHA-256 is identical."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip1 = Path(tmpdir) / "canary1.zip"
        zip2 = Path(tmpdir) / "canary2.zip"

        create_synthetic_canary(zip1, level_name="synthetic_canary")
        create_synthetic_canary(zip2, level_name="synthetic_canary")

        sha1 = hashlib.sha256(zip1.read_bytes()).hexdigest()
        sha2 = hashlib.sha256(zip2.read_bytes()).hexdigest()

        assert sha1 == sha2, f"ZIPs are not deterministic: {sha1} != {sha2}"


def test_canary_zip_entry_timestamps():
    """Verify all ZIP entries have fixed timestamps (no wall-clock)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_zip = Path(tmpdir) / "canary.zip"
        create_synthetic_canary(output_zip, level_name="synthetic_canary")

        with zipfile.ZipFile(output_zip, 'r') as zf:
            for info in zf.infolist():
                # Fixed timestamp should be 1980-01-01 00:00:00
                assert info.date_time == (1980, 1, 1, 0, 0, 0), \
                    f"Entry {info.filename} has nondeterministic timestamp: {info.date_time}"


def test_canary_zip_entries_sorted():
    """Verify ZIP entries are in sorted order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_zip = Path(tmpdir) / "canary.zip"
        create_synthetic_canary(output_zip, level_name="synthetic_canary")

        with zipfile.ZipFile(output_zip, 'r') as zf:
            names = zf.namelist()
            assert names == sorted(names), "ZIP entries are not sorted"


if __name__ == "__main__":
    test_import_create_synthetic_canary()
    print("test_import_create_synthetic_canary passed")
    test_canary_zip_structure()
    print("test_canary_zip_structure passed")
    test_canary_determinism()
    print("test_canary_determinism passed")
    test_canary_zip_entry_timestamps()
    print("test_canary_zip_entry_timestamps passed")
    test_canary_zip_entries_sorted()
    print("test_canary_zip_entries_sorted passed")
