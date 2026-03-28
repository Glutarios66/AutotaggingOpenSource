"""
In-memory job store.
Tracks the state of every processing job by job_id.
"""

jobs: dict = {}


def create_job(job_id: str, params: dict = None):
    jobs[job_id] = {
        "status": "processing",
        "file_path": None,
        "filename": None,
        "params": params or {},
        "stats": None,
        "error": None
    }


def complete_job(job_id: str, file_path: str, filename: str, stats: dict = None):
    jobs[job_id]["status"] = "done"
    jobs[job_id]["file_path"] = file_path
    jobs[job_id]["filename"] = filename
    jobs[job_id]["stats"] = stats or {}


def fail_job(job_id: str, error: str):
    jobs[job_id]["status"] = "error"
    jobs[job_id]["error"] = error


def get_job(job_id: str) -> dict | None:
    return jobs.get(job_id)