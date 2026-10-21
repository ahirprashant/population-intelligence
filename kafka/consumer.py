import json
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    "population-events",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    group_id=None,
)

print("Listening for population events... Press Ctrl+C to stop.")

try:
    for message in consumer:
        try:
            if not message.value:
                print("Skipping empty message.")
                continue

            event = json.loads(message.value.decode("utf-8"))
            print(json.dumps(event, indent=2))

        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            print(f"Skipping invalid message at offset {message.offset}: {error}")

except KeyboardInterrupt:
    print("\nConsumer stopped.")

finally:
    consumer.close()
