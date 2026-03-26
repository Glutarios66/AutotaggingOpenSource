jobs = {}


def create_job(job_id, params=None):
    jobs[job_id] = {
        "status": "processing",
        "file_path": None,
        "filename": None,
        "params": params or {},
        "error": None
    }


def complete_job(job_id, file_path, filename):
    jobs[job_id]["status"] = "done"
    jobs[job_id]["file_path"] = file_path
    jobs[job_id]["filename"] = filename


def fail_job(job_id, error):
    jobs[job_id]["status"] = "error"
    jobs[job_id]["error"] = error


def get_job(job_id):
    return jobs.get(job_id)