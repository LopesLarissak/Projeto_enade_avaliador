
import logging
from confluent_kafka import Producer
from app.config import KAFKA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPIC = "enade.questions"


def publish_questions(questions):
    producer = Producer({
        "bootstrap.servers": KAFKA,
        "enable.idempotence": True,
        "acks": "all",
        "retries": 10,
        "max.in.flight.requests.per.connection": 5
    })

    delivered = []
    failed = []

    def delivery_report(error, message):
        if error is not None:
            failed.append(str(error))
            logger.error("Falha na publicação: %s", error)
        else:
            delivered.append(message.key().decode("utf-8"))
            logger.info(
                "Questão publicada: %s | Partição: %s",
                message.key().decode("utf-8"),
                message.partition()
            )

    for question in questions:
        question_id = str(question.id)

        payload = question.model_dump_json().encode("utf-8")

        while True:
            try:
                producer.produce(
                    topic=TOPIC,
                    key=question_id.encode("utf-8"),
                    value=payload,
                    on_delivery=delivery_report
                )
                break
            except BufferError:
                logger.warning("Fila Kafka cheia. Aguardando...")
                producer.poll(1)

        producer.poll(0)

    remaining = producer.flush(30)

    if remaining > 0 or failed:
        raise RuntimeError(
            f"Falha na publicação Kafka: "
            f"{remaining} mensagens pendentes; "
            f"{len(failed)} erros de entrega."
        )

    logger.info(
        "Publicação concluída: %s questões entregues.",
        len(delivered)
    )

    return len(delivered)
