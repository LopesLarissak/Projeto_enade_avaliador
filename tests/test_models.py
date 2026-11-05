from app.models import stable_question_id


def test_idempotent_id():
    assert stable_question_id("prova.pdf", 2, 1, "Questão teste") == stable_question_id("prova.pdf", 2, 1, "Questão teste")
