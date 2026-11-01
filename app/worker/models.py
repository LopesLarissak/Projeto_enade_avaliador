from pydantic import BaseModel, Field
from typing import Literal
from uuid import uuid5, NAMESPACE_URL

class Question(BaseModel):
    id: str
    source_pdf: str
    source_page: int
    area: str = "Não identificado"
    course: str = "Não identificado"
    year: int | None = None
    exam_type: Literal["FG", "CE", "Não identificado"] = "Não identificado"
    question_type: Literal["objetiva", "discursiva", "não_identificada"] = "não_identificada"
    statement: str
    alternatives: list[str] = Field(default_factory=list)
    answer_key: str | None = None
    annulled: bool = False
    knowledge_objects: list[str] = Field(default_factory=list)
    competencies: list[str] = Field(default_factory=list)
    media_review_required: bool = False
    extraction_status: str = "needs_review"

def stable_question_id(pdf_name: str, page: int, ordinal: int, text: str) -> str:
    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return str(uuid5(NAMESPACE_URL, f"{pdf_name}:{page}:{ordinal}:{digest}"))
