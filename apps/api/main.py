import os
import json
import uuid
import hashlib
import asyncio
from pathlib import Path
from typing import Literal, Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

# ImportTriWorld compiler & validator modules
from packages.compiler.synthetic_canary import create_synthetic_canary
from packages.compiler.zip_validator import validate_zip_structure

app = FastAPI(
    title="TriWorld API",
    description="Local HTTP API Bridge for TriWorld Procedural Map Compiler",
    version="0.1.0",
)

# CORS configuration for local development origins
origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(r"C:\TriWorld")
RUNTIME_JOBS_DIR = BASE_DIR / "runtime_jobs"
RUNTIME_JOBS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory status cache backed by disk status.json
jobs_db: Dict[str, Dict[str, Any]] = {}

SIZE_MAP = {
    "S": 512,
    "M": 1024,
    "L": 2048,
    "XL": 4096,
}


class GenerateRequest(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    size: Literal["S", "M", "L", "XL"]
    extentMeters: float

    @field_validator("extentMeters")
    @classmethod
    def validate_extent(cls, v: float, info) -> float:
        size_key = info.data.get("size")
        if size_key and size_key in SIZE_MAP:
            expected = SIZE_MAP[size_key]
            if abs(v - expected) > 0.01:
                raise ValueError(f"extentMeters {v} does not match size {size_key} (expected {expected})")
        return v


class GenerateResponse(BaseModel):
    jobId: str
    status: str


class JobStatusResponse(BaseModel):
    jobId: str
    status: Literal["queued", "running", "completed", "failed"]
    stage: str
    progress: float
    error: Optional[str] = None
    downloadUrl: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "compiler": "synthetic-canary",
    }


def save_job_disk_artifacts(job_dir: Path, request_data: dict, status_data: dict):
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "request.json").write_text(json.dumps(request_data, indent=2))
    (job_dir / "status.json").write_text(json.dumps(status_data, indent=2))


def process_job_task(job_id: str, request_data: dict):
    job_dir = RUNTIME_JOBS_DIR / job_id
    zip_path = job_dir / f"triworld-synthetic-canary-{job_id}.zip"

    def update(stage: str, progress: float, status_str: str = "running", error: Optional[str] = None, download_url: Optional[str] = None):
        job_info = jobs_db.get(job_id, {})
        job_info.update({
            "status": status_str,
            "stage": stage,
            "progress": progress,
            "error": error,
            "downloadUrl": download_url,
        })
        jobs_db[job_id] = job_info
        save_job_disk_artifacts(job_dir, request_data, job_info)

    try:
        # Stage 1: Preparing area
        update("Preparing area", 10.0)
        import time
        time.sleep(0.4)

        # Stage 2: Building synthetic canary
        update("Building synthetic canary", 40.0)
        file_hashes = create_synthetic_canary(zip_path, "synthetic_canary")
        zip_bytes = zip_path.read_bytes()
        zip_sha256 = hashlib.sha256(zip_bytes).hexdigest()
        (job_dir / "candidate-sha256.txt").write_text(zip_sha256)
        time.sleep(0.4)

        # Stage 3: Validating BeamNG package
        update("Validating BeamNG package", 75.0)
        report = validate_zip_structure(zip_path)
        val_txt = f"Validation Report for {zip_path.name}:\nAll Passed: {report.all_passed}\nChecks: {len(report.checks)}\n"
        for c in report.checks:
            val_txt += f"  [{'PASS' if c.passed else 'FAIL'}] {c.check_name}: {c.message}\n"
        (job_dir / "validator-result.txt").write_text(val_txt)

        if not report.all_passed:
            raise ValueError(f"Zip validation failed for {zip_path.name}")

        time.sleep(0.3)

        # Stage 4: Ready (Completed)
        dl_url = f"/api/jobs/{job_id}/download"
        update("Ready", 100.0, status_str="completed", download_url=dl_url)

    except Exception as e:
        err_msg = str(e)
        update("failed", 0.0, status_str="failed", error=err_msg)


@app.post("/api/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_dir = RUNTIME_JOBS_DIR / job_id
    req_dict = req.model_dump()

    initial_job_info = {
        "jobId": job_id,
        "status": "queued",
        "stage": "Preparing area",
        "progress": 0.0,
        "error": None,
        "downloadUrl": None,
    }

    jobs_db[job_id] = initial_job_info
    save_job_disk_artifacts(job_dir, req_dict, initial_job_info)

    background_tasks.add_task(process_job_task, job_id, req_dict)

    return GenerateResponse(jobId=job_id, status="queued")


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    # Check in-memory DB or fallback to disk status.json
    job_info = jobs_db.get(job_id)
    if not job_info:
        status_file = RUNTIME_JOBS_DIR / job_id / "status.json"
        if status_file.exists():
            job_info = json.loads(status_file.read_text())
            jobs_db[job_id] = job_info
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(**job_info)


@app.get("/api/jobs/{job_id}/download")
def download_job_zip(job_id: str):
    job_dir = RUNTIME_JOBS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    status_file = job_dir / "status.json"
    if status_file.exists():
        job_info = json.loads(status_file.read_text())
        if job_info.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Job compilation is not completed yet")

    zip_path = job_dir / f"triworld-synthetic-canary-{job_id}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Generated ZIP file not found")

    # Safe path check to prevent arbitrary filesystem traversal
    if not zip_path.resolve().is_relative_to(RUNTIME_JOBS_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"triworld-synthetic-canary-{job_id}.zip",
    )
