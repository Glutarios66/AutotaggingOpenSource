from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class ElementType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    TABLE = "table"
    LIST = "list"


class Heading(BaseModel):
    type: ElementType = ElementType.HEADING
    level: int          # 1 = H1, 2 = H2, 3 = H3 ...
    text: str
    page: int


class Paragraph(BaseModel):
    type: ElementType = ElementType.PARAGRAPH
    text: str
    page: int


class Image(BaseModel):
    type: ElementType = ElementType.IMAGE
    index: int          # position in document
    page: int
    alt_text: Optional[str] = None   # filled by alt_text processor later
    image_bytes: Optional[bytes] = None


class TableCell(BaseModel):
    text: str
    is_header: bool = False


class Table(BaseModel):
    type: ElementType = ElementType.TABLE
    page: int
    rows: List[List[TableCell]]


class ListItem(BaseModel):
    text: str
    level: int = 0


class DocumentList(BaseModel):
    type: ElementType = ElementType.LIST
    page: int
    items: List[ListItem]


# Union type for all elements
DocumentElement = Heading | Paragraph | Image | Table | DocumentList


class UnifiedDocument(BaseModel):
    filename: str
    total_pages: int
    language: Optional[str] = "en"
    elements: List[DocumentElement] = []

    # Summary counts — filled after parsing
    heading_count: int = 0
    paragraph_count: int = 0
    image_count: int = 0
    table_count: int = 0

    def compute_stats(self):
        self.heading_count = sum(1 for e in self.elements if isinstance(e, Heading))
        self.paragraph_count = sum(1 for e in self.elements if isinstance(e, Paragraph))
        self.image_count = sum(1 for e in self.elements if isinstance(e, Image))
        self.table_count = sum(1 for e in self.elements if isinstance(e, Table))