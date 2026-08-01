import sys
import hashlib
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app, RUNTIME_JOBS_DIR
from packages.compiler.zip_validator import validate_zip_structure

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["compiler"] == "synthetic-canary"


def test_generate_input_validation():
    # Valid request
    valid_payload = {
        "latitude": 48.7,
        "longitude": 18.3,
        "size": "S",
        "extentMeters": 512.0,
    }
    res = client.post("/api/generate", json=valid_payload)
    assert res.status_code == 202
    data = res.json()
    assert "jobId" in data
    assert data["status"] == "queued"

    # Mismatched extent for size
    invalid_extent_payload = {
        "latitude": 48.7,
        "longitude": 18.3,
        "size": "S",
        "extentMeters": 1024.0,
    }
    res_inv = client.post("/api/generate", json=invalid_extent_payload)
    assert res_inv.status_code == 422

    # Out of range latitude
    invalid_lat_payload = {
        "latitude": 95.0,
        "longitude": 18.3,
        "size": "M",
        "extentMeters": 1024.0,
    }
    res_lat = client.post("/api/generate", json=invalid_lat_payload)
    assert res_lat.status_code == 422


def test_end_to_end_job_compilation_and_download():
    payload = {
        "latitude": 48.7,
        "longitude": 18.3,
        "size": "M",
        "extentMeters": 1024.0,
    }
    res = client.post("/api/generate", json=payload)
    assert res.status_code == 202
    job_id = res.json()["jobId"]

    # Poll status until completed
    import time
    completed = False
    status_data = {}
    for _ in range(30):
        s_res = client.get(f"/api/jobs/{job_id}")
        assert s_res.status_code == 200
        status_data = s_res.json()
        if status_data["status"] == "completed":
            completed = True
            break
        time.sleep(0.2)

    assert completed is True
    assert status_data["stage"] == "Ready"
    assert status_data["progress"] == 100.0
    assert status_data["downloadUrl"] == f"/api/jobs/{job_id}/download"

    # Download ZIP
    dl_res = client.get(f"/api/jobs/{job_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/zip"

    downloaded_bytes = dl_res.content
    assert len(downloaded_bytes) > 0

    downloaded_sha256 = hashlib.sha256(downloaded_bytes).hexdigest()

    # Verify against candidate-sha256.txt on disk
    job_dir = RUNTIME_JOBS_DIR / job_id
    stored_hash = (job_dir / "candidate-sha256.txt").read_text().strip()
    assert downloaded_sha256 == stored_hash

    # Validate downloaded ZIP using production zip_validator
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(downloaded_bytes)
        tmp_path = Path(tmp.name)

    try:
        report = validate_zip_structure(tmp_path)
        assert report.all_passed is True
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
