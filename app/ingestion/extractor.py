from pathlib import Path
import re
import fitz
from app.models import Question, stable_question_id

QUESTION_RE = re.compile(r"(?im)^\s*(?:QUESTÃO|QUESTAO)\s*(\d{1,3})\s*[:.-]?\s*$")

def extract_questions(pdf_path: Path, year: int | None = None, course: str = "Não identificado",
                      area: str = "Não identificado", exam_type: str = "Não identificado"):
    doc = fitz.open(pdf_path)
    output = []
    for page_index, page in enumerate(doc, start=1):
        text = page.get_text("text")
        matches = list(QUESTION_RE.finditer(text))
        if not matches and text.strip():
            # Não inventa segmentação: registra a página como item para revisão.
            chunks = [(0, len(text), None)]
        else:
            chunks = [(m.start(), matches[i+1].start() if i+1 < len(matches) else len(text), m.group(1))
                      for i, m in enumerate(matches)]
        for ordinal, (start, end, number) in enumerate(chunks, start=1):
            statement = text[start:end].strip()
            if not statement:
                continue
            alternatives = re.findall(r"(?m)^\s*([A-E])\)\s*(.+)$", statement)
            output.append(Question(
                id=stable_question_id(pdf_path.name, page_index, ordinal, statement),
                source_pdf=pdf_path.name, source_page=page_index, area=area,
                course=course, year=year, exam_type=exam_type,
                question_type="objetiva" if alternatives else "não_identificada",
                statement=statement,
                alternatives=[f"{a}) {b}" for a,b in alternatives],
                media_review_required=bool(page.get_images(full=True)),
                extraction_status="needs_review" if number is None or page.get_images(full=True) else "extracted"
            ))
    return output
