import json
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "population-events"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
)

event = {
    "district": "Surat",
    "year": 2011,
    "population": 6081322,
    "event_type": "population_update",
    "source": "simulated",
}

try:
    result = producer.send(TOPIC, value=event).get(timeout=10)
    print(f"Event sent to topic: {result.topic}")
    print(f"Partition: {result.partition}")
    print(f"Offset: {result.offset}")
    print(f"Event: {json.dumps(event)}")
finally:
    producer.close()
