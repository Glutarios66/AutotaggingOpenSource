import time
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Optional
import os

from api.models import ProcessResponse, AccessibilityReport, WCAGLevel

router = APIRouter()

ALLOWED_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
MAX_FILE_SIZE_MB = 100


@router.post("/process", response_model=ProcessResponse)
async def process_document(
    file: UploadFile = File(...),
    generate_report: bool = Form(False),
    shift_headings: bool = Form(False),
    wcag_level: str = Form("AA"),
):
    start_time = time.time()

    # --- Validierung ---
    if file.content_type not in ALLOWED_TYPES:
        return ProcessResponse(
            status="error",
            filename=file.filename,
            message=f"Unsupported file type: {file.content_type}. Only PDF and DOCX allowed."
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        return ProcessResponse(
            status="error",
            filename=file.filename,
            message=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB."
        )

    # --- Pipeline (wird Schritt für Schritt gefüllt) ---
    # Phase 2: from parser.document import parse
    # Phase 3: from processors.alt_text import AltTextProcessor
    # Phase 4: from checker.wcag import WCAGChecker

    processing_time = int((time.time() - start_time) * 1000)

    # Platzhalter-Response bis Pipeline gebaut ist
    report = None
    if generate_report:
        report = AccessibilityReport(
            wcag_score=0,
            wcag_level=wcag_level,
            violations_found=0,
            violations_fixed=0,
            violations=[],
            processors_applied=[],
            processing_time_ms=processing_time
        )

    return ProcessResponse(
        status="received",
        filename=file.filename,
        report=report,
        message="File received. Processing pipeline coming soon."
    )


@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    file_path = f"output/{job_id}/{filename}"
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    return FileResponse(file_path, filename=filename)