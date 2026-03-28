import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import os

from services.job_store import create_job, get_job
from services.pipeline import run_pipeline

router = APIRouter()

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]
MAX_FILE_SIZE_MB = 100


@router.post("/process")
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    generate_report: bool = Form(False),
    shift_headings: bool = Form(False),
    wcag_level: str = Form("AA"),
):
    # --- Validation ---
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Only PDF and DOCX allowed."
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB."
        )

    # --- Create job and hand off to pipeline ---
    job_id = str(uuid.uuid4())
    create_job(job_id, {
        "generate_report": generate_report,
        "shift_headings": shift_headings,
        "wcag_level": wcag_level,
        "filename": file.filename
    })

    background_tasks.add_task(
        run_pipeline,
        job_id,
        content,
        file.filename,
        file.content_type,
        generate_report,
        shift_headings,
        wcag_level
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "status_url": f"/status/{job_id}",
        "download_url": f"/download/{job_id}"
    }


@router.get("/status/{job_id}")
def get_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/download/{job_id}")
def download_file(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job is not done yet. Status: {job['status']}")

    file_path = job["file_path"]
    filename = job["filename"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(file_path, filename=filename, media_type="application/pdf")

