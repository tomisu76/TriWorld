"""Job Queue - SQLite-backed persistent job queue with state machine."""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from packages.contracts.job_state import JobStatus, STAGE_ORDER, compute_overall_progress


class JobQueue:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    request_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stage TEXT,
                    stage_progress REAL DEFAULT 0.0,
                    overall_progress REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    updated_at TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    error_json TEXT,
                    request_json TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT,
                    metrics_json TEXT,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    sha256 TEXT,
                    bytes INTEGER,
                    kind TEXT,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_job_events_job_id ON job_events(job_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_job_artifacts_job_id ON job_artifacts(job_id)")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_job(self, request: dict, request_hash: str, workspace: Path) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO jobs (job_id, request_hash, status, stage, stage_progress, overall_progress,
                                 created_at, updated_at, workspace, request_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, request_hash, JobStatus.QUEUED.value, None, 0.0, 0.0,
                  now, now, str(workspace), json.dumps(request, separators=(',', ':'))))
        return job_id

    def update_job(self, job_id: str, status: Optional[JobStatus] = None,
                   stage: Optional[str] = None, stage_progress: Optional[float] = None,
                   error: Optional[str] = None):
        with self._conn() as conn:
            row = conn.execute("SELECT status, stage, stage_progress FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row:
                raise ValueError(f"Job {job_id} not found")
            
            new_status = status.value if status else row['status']
            new_stage = stage if stage is not None else row['stage']
            new_stage_progress = stage_progress if stage_progress is not None else row['stage_progress']
            
            overall = compute_overall_progress(new_stage or "", new_stage_progress)
            
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute("""
                UPDATE jobs SET status = ?, stage = ?, stage_progress = ?, overall_progress = ?,
                               updated_at = ?, error_json = ?
                WHERE job_id = ?
            """, (new_status, new_stage, new_stage_progress, overall, now,
                  json.dumps(error) if error else None, job_id))

    def add_event(self, job_id: str, stage: str, message: str, metrics: Dict[str, Any] = None):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO job_events (job_id, stage, timestamp, message, metrics_json)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, stage, datetime.utcnow().isoformat() + "Z", message,
                  json.dumps(metrics, separators=(',', ':')) if metrics else None))

    def add_artifact(self, job_id: str, path: Path, sha256: str, bytes_: int, kind: str):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO job_artifacts (job_id, path, sha256, bytes, kind)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, str(path), sha256, bytes_, kind))

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            return dict(row) if row else None

    def get_events(self, job_id: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM job_events WHERE job_id = ? ORDER BY id", (job_id,)).fetchall()
            events = []
            for r in rows:
                event = dict(r)
                if event.get('metrics_json'):
                    event['metrics'] = json.loads(event['metrics_json'])
                else:
                    event['metrics'] = {}
                del event['metrics_json']
                events.append(event)
            return events

    def get_artifacts(self, job_id: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM job_artifacts WHERE job_id = ?", (job_id,)).fetchall()
            return [dict(r) for r in rows]

    def list_jobs(self, status: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            if status:
                rows = conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC", (status.value,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def find_incomplete_jobs(self) -> List[Dict[str, Any]]:
        """Find jobs that were interrupted (non-terminal states)."""
        with self._conn() as conn:
            placeholders = ','.join('?' for _ in [s.value for s in [JobStatus.READY, JobStatus.FAILED, JobStatus.CANCELLED]])
            query = f"SELECT * FROM jobs WHERE status NOT IN ({placeholders}) ORDER BY created_at"
            rows = conn.execute(query, [s.value for s in [JobStatus.READY, JobStatus.FAILED, JobStatus.CANCELLED]]).fetchall()
            return [dict(r) for r in rows]