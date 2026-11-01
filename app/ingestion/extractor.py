
from pathlib import Path
import re
import fitz

from app.models import Question, stable_question_id


# Reconhece, por exemplo:
# QUESTÃO 06
# QUESTAO 6
# QUESTÃO DISCURSIVA 02
# QUESTAO DISCURSIVA 2
QUESTION_RE = re.compile(
    r"(?im)^[ \t]*QUEST(?:Ã|A)O[ \t]+"
    r"(?:(DISCURSIVA)[ \t]+)?"
    r"0*(\d{1,3})[ \t]*"
    r"(?:[:.\-][ \t]*)?$"
)


def normalize_text(text: str) -> str:
    """Normaliza quebras e espaços sem remover o conteúdo da questão."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_alternatives(statement: str) -> list[str]:
    """
    Reconhece alternativas em formatos como:
    A) Texto
    A. Texto
    A
    Texto da alternativa
    """
    lines = statement.splitlines()
    alternatives = []
    current_label = None
    current_text = []

    label_re = re.compile(r"^\s*([A-E])\s*(?:[).:\-]\s*(.*))?$", re.I)

    for line in lines:
        line = line.strip()
        match = label_re.match(line)

        if match:
            if current_label:
                content = " ".join(current_text).strip()
                alternatives.append(f"{current_label}) {content}".strip())

            current_label = match.group(1).upper()
            initial_text = match.group(2) or ""
            current_text = [initial_text] if initial_text else []
        elif current_label and line:
            current_text.append(line)

    if current_label:
        content = " ".join(current_text).strip()
        alternatives.append(f"{current_label}) {content}".strip())

    return alternatives


def extract_questions(
    pdf_path: Path,
    year: int | None = None,
    course: str = "Não identificado",
    area: str = "Não identificado",
    exam_type: str = "Não identificado"
):
    doc = fitz.open(pdf_path)

    output = []
    current = None
    ordinal = 0

    def finish_question():
        nonlocal current, ordinal

        if current is None:
            return

        statement = normalize_text(current["text"])

        if not statement:
            current = None
            return

        ordinal += 1

        if current["type"] == "discursiva":
            question_type = "discursiva"
            alternatives = []
        else:
            question_type = "objetiva"
            alternatives = extract_alternatives(statement)

        pages = current["pages"]
        has_images = any(
            bool(doc[page_number - 1].get_images(full=True))
            for page_number in pages
        )

        # Questões com cabeçalho explícito são identificadas.
        # A presença de imagens exige conferência complementar.
        status = "needs_review" if has_images else "extracted"

        question = Question(
            id=stable_question_id(
                pdf_path.name,
                current["start_page"],
                ordinal,
                statement
            ),
            source_pdf=pdf_path.name,
            source_page=current["start_page"],
            area=area,
            course=course,
            year=year,
            exam_type=exam_type,
            question_type=question_type,
            statement=statement,
            alternatives=alternatives,
            media_review_required=has_images,
            extraction_status=status
        )

        output.append(question)
        current = None

    for page_number, page in enumerate(doc, start=1):
        page_text = normalize_text(page.get_text("text"))

        if not page_text:
            continue

        matches = list(QUESTION_RE.finditer(page_text))

        # Se a página não tiver novo cabeçalho, pode ser
        # continuação da questão iniciada na página anterior.
        if not matches:
            if current is not None:
                current["text"] += "\n" + page_text
                current["pages"].add(page_number)
            continue

        # Texto anterior ao primeiro cabeçalho pode ser
        # continuação da questão anterior.
        prefix = page_text[:matches[0].start()].strip()

        if prefix and current is not None:
            current["text"] += "\n" + prefix
            current["pages"].add(page_number)

        for index, match in enumerate(matches):
            finish_question()

            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(page_text)
            )

            block = page_text[match.end():end].strip()

            is_discursive = bool(match.group(1))
            question_number = match.group(2)

            current = {
                "text": block,
                "start_page": page_number,
                "pages": {page_number},
                "number": question_number,
                "type": "discursiva" if is_discursive else "objetiva"
            }

    # Finaliza a última questão do documento.
    finish_question()

    doc.close()
    return output

