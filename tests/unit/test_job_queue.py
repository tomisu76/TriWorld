import tempfile
import os
from pathlib import Path

from packages.compiler.job_queue import JobQueue
from packages.contracts.job_state import JobStatus


def test_job_queue():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "jobs.db"
        queue = JobQueue(db_path)
        
        # Create a job
        request = {"name": "test_map", "center": {"lat": 0, "lon": 0}, "extent": {"widthM": 100, "heightM": 100}}
        request_hash = "abc123"
        workspace = Path(tmpdir) / "workspace"
        
        job_id = queue.create_job(request, request_hash, workspace)
        assert job_id is not None
        
        # Get job
        job = queue.get_job(job_id)
        assert job is not None
        assert job['status'] == JobStatus.QUEUED.value
        assert job['request_hash'] == request_hash
        
        # Update job
        queue.update_job(job_id, status=JobStatus.VALIDATING_REQUEST, stage="validating_request", stage_progress=0.5)
        job = queue.get_job(job_id)
        assert job['status'] == JobStatus.VALIDATING_REQUEST.value
        assert job['stage'] == "validating_request"
        assert job['stage_progress'] == 0.5
        assert job['overall_progress'] > 0
        
        # Add event
        queue.add_event(job_id, "validating_request", "Validating request", {"checks": 5})
        events = queue.get_events(job_id)
        assert len(events) == 1
        assert events[0]['message'] == "Validating request"
        assert events[0]['metrics']['checks'] == 5
        
        # Add artifact
        workspace.mkdir(parents=True, exist_ok=True)
        artifact_path = workspace / "test.txt"
        artifact_path.write_text("hello")
        queue.add_artifact(job_id, artifact_path, "sha256abc", 5, "test")
        artifacts = queue.get_artifacts(job_id)
        assert len(artifacts) == 1
        assert artifacts[0]['sha256'] == "sha256abc"
        
        # Complete job
        queue.update_job(job_id, status=JobStatus.READY, stage="auditing_zip", stage_progress=1.0)
        job = queue.get_job(job_id)
        assert job['status'] == JobStatus.READY.value
        assert job['overall_progress'] == 1.0
        
        # List jobs
        jobs = queue.list_jobs()
        assert len(jobs) == 1
        
        # Find incomplete jobs (none should be found)
        incomplete = queue.find_incomplete_jobs()
        assert len(incomplete) == 0
        
        print("All tests passed")


if __name__ == "__main__":
    test_job_queue()