from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class WCAGLevel(str, Enum):
    A = "A"
    AA = "AA"
    AAA = "AAA"


class ProcessRequest(BaseModel):
    generate_report: bool = False
    shift_headings: bool = False
    wcag_level: WCAGLevel = WCAGLevel.AA


class Violation(BaseModel):
    rule: str
    description: str
    element: str
    page: Optional[int] = None
    fix_applied: Optional[str] = None


class AccessibilityReport(BaseModel):
    wcag_score: int
    wcag_level: str
    violations_found: int
    violations_fixed: int
    violations: List[Violation]
    processors_applied: List[str]
    processing_time_ms: int


class ProcessResponse(BaseModel):
    status: str
    filename: str
    tagged_pdf_url: Optional[str] = None
    report: Optional[AccessibilityReport] = None
    message: Optional[str] = None