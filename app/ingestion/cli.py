import argparse
from pathlib import Path
from app.ingestion.extractor import extract_questions
from app.ingestion.producer import publish_questions

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--year", type=int)
    p.add_argument("--course", default="Não identificado")
    p.add_argument("--area", default="Não identificado")
    p.add_argument("--exam-type", default="Não identificado", choices=["FG","CE","Não identificado"])
    a = p.parse_args()
    pdfs = list(Path(a.input).glob("*.pdf"))
    total = 0
    for pdf in pdfs:
        questions = extract_questions(pdf, a.year, a.course, a.area, a.exam_type)
        publish_questions(questions)
        total += len(questions)
        print(f"{pdf.name}: {len(questions)} registros publicados")
    print(f"Total publicado: {total}")
if __name__ == "__main__": main()
