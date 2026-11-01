import json, time
from confluent_kafka import Producer
from app.config import KAFKA

def publish_questions(questions):
    producer = Producer({"bootstrap.servers": KAFKA, "enable.idempotence": True,
                         "acks": "all", "retries": 10})
    for q in questions:
        producer.produce("enade.questions", key=q.id, value=q.model_dump_json().encode())
        producer.poll(0)
    producer.flush(30)
