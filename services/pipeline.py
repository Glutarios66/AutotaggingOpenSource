import os
from parser.document import parse_document
from services.job_store import complete_job, fail_job


def run_pipeline(
    job_id: str,
    content: bytes,
    filename: str,
    content_type: str,
    generate_report: bool = False,
    shift_headings: bool = False,
    wcag_level: str = "AA"
):
    """
    Main processing pipeline.
    Called as a background task from routes.py.

    Steps:
      1. Parse document into Unified IR
      2. Run processors (alt_text, structure, language) — Phase 3
      3. Run WCAG checker — Phase 4
      4. Render output file
      5. Mark job as done
    """
    try:
        # --- Step 1: Parse ---
        unified_doc = parse_document(content, filename, content_type)

        # --- Step 2: Processors (Phase 3) ---
        # from processors.alt_text import AltTextProcessor
        # from processors.structure import StructureProcessor
        # from processors.language import LanguageProcessor
        #
        # processors = [
        #     AltTextProcessor(),
        #     StructureProcessor(shift_headings=shift_headings),
        #     LanguageProcessor(),
        # ]
        # for processor in processors:
        #     unified_doc = processor.process(unified_doc)

        # --- Step 3: WCAG Checker (Phase 4) ---
        # from checker.wcag import WCAGChecker
        # report = WCAGChecker(level=wcag_level).check(unified_doc)

        # --- Step 4: Render output ---
        # from renderer.document import render_document
        # output_bytes = render_document(unified_doc)
        #
        # For now: write original file as placeholder output
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_autotagged{ext}"
        output_dir = f"output/{job_id}"
        output_path = f"{output_dir}/{output_filename}"
        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(content)

        # --- Step 5: Mark job complete ---
        complete_job(job_id, output_path, output_filename, stats={
            "headings": unified_doc.heading_count,
            "paragraphs": unified_doc.paragraph_count,
            "images": unified_doc.image_count,
            "tables": unified_doc.table_count,
        })

    except Exception as e:
        fail_job(job_id, str(e))