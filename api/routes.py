import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os

from api.models import ProcessResponse, AccessibilityReport
from parser.document import parse_document
import uuid
from renderer.document import highlight_elements
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
from core.job_store import create_job, complete_job, fail_job
router = APIRouter()

ALLOWED_TYPES = [
    "application/pdf"
]
MAX_FILE_SIZE_MB = 100

@router.post("/process")
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    generate_report: bool = Form(False),
    shift_headings: bool = Form(False),
):
    content = await file.read()

    job_id = str(uuid.uuid4())
    create_job(job_id, {
        "generate_report": generate_report,
        "shift_headings": shift_headings
    })

    background_tasks.add_task(
        process_file,
        job_id,
        content,
        file.filename,
        file.content_type,
        generate_report,
        shift_headings
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "parameters": {
            "generate_report": generate_report,
            "shift_headings": shift_headings
        },
        "status_url": f"/status/{job_id}",
        "download_url": f"/download/{job_id}"
    }

"""
@router.post("/process", response_model=ProcessResponse)
async def process_document(
    file: UploadFile = File(...),
    generate_report: bool = Form(False),
    shift_headings: bool = Form(False),
):
    start_time = time.time()

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

    # --- Phase 2: Parse document into Unified IR ---
    try:
        # --- Parse ---
        unified_doc = parse_document(content, file.filename, file.content_type)

        # --- Output vorbereiten ---
        job_id = str(uuid.uuid4())

        name, ext = os.path.splitext(file.filename)
        output_filename = f"{name}_autotagged{ext}"

        output_dir = f"output/{job_id}"
        output_path = f"{output_dir}/{output_filename}"

        os.makedirs(output_dir, exist_ok=True)

        # --- Renderer ---
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

    processing_time = int((time.time() - start_time) * 1000)

    # --- Phase 3: Processors (coming soon) ---
    # from processors.alt_text import AltTextProcessor
    # from processors.structure import StructureProcessor

    # --- Phase 4: WCAG Checker (coming soon) ---
    # from checker.wcag import WCAGChecker

    # --- Build report ---
    report = None
    if generate_report:
        report = AccessibilityReport(
            wcag_score=0,
            violations_found=0,
            violations_fixed=0,
            violations=[],
            processors_applied=["parser"],
            processing_time_ms=processing_time
        )

    return ProcessResponse(
        status="done",
        filename=file.filename,
        tagged_pdf_url=f"/download/{job_id}/{output_filename}",
        report=report,
        message=(
            f"Document parsed & annotated. "
            f"Found {unified_doc.heading_count} headings, "
            f"{unified_doc.paragraph_count} paragraphs, "
            f"{unified_doc.image_count} images, "
            f"{unified_doc.table_count} tables."
        )
    )
"""
def process_file(
    job_id,
    content,
    filename,
    content_type,
    generate_report,
    shift_headings
):
    import os
    from parser.document import parse_document
    from renderer.document import highlight_elements

    try:
        unified_doc = parse_document(content, filename, content_type)

        if shift_headings:
            print("Shift headings enabled")

        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_autotagged{ext}"

        output_dir = f"output/{job_id}"
        os.makedirs(output_dir, exist_ok=True)

        output_path = f"{output_dir}/{output_filename}"

        complete_job(job_id, output_path, output_filename)

    except Exception as e:
        fail_job(job_id, str(e))
"""
@router.post("/process")
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    content = await file.read()

    job_id = str(uuid.uuid4())
    create_job(job_id)

    background_tasks.add_task(
        process_file,
        job_id,
        content,
        file.filename,
        file.content_type
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "download_url": f"/download/{job_id}"
    }
"""
@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    file_path = f"output/{job_id}/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

@router.get("/status/{job_id}")
def get_status(job_id: str):
    from core.job_store import get_job

    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job