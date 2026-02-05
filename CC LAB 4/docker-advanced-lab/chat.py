import pika
import threading
import os
import time
import sys
import json

# =========================
# Environment Variables
# =========================
RABBIT_HOST = os.getenv('RABBIT_HOST', 'localhost')
QUEUE_NAME = os.getenv('QUEUE_NAME', 'chat_queue')
TARGET_QUEUE = os.getenv('TARGET_QUEUE')
USER_NAME = os.getenv('USER_NAME', 'unknown-user')
HISTORY_FILE = "/app/data/history.txt"
STANDALONE_MODE = os.getenv('STANDALONE_MODE', 'false').lower() == 'true'

os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

# =========================
# Utility Functions
# =========================
def save_to_history(message):
    with open(HISTORY_FILE, "a") as f:
        f.write(message + "\n")

def display_history():
    if os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 0:
        print("\n--- Chat History ---")
        with open(HISTORY_FILE, "r") as f:
            print(f.read(), end="")
        print("--- End of History ---\n")
    else:
        print("\n--- No Previous Chat History ---\n")

# =========================
# RabbitMQ Consumer Callback
# =========================
def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        sender = data.get("sender", "unknown")
        message = data.get("message", "")

        log = f"Received from {sender}: {message}"
        print(f"\n{log}\nType message: ", end="", flush=True)
        save_to_history(log)

    except Exception as e:
        print("Error decoding message:", e)

# =========================
# RabbitMQ Connection
# =========================
def get_connection():
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            print(f"RabbitMQ not ready, retrying... ({retry_count}/{max_retries})")
            time.sleep(2)

    print(f"\nERROR: Could not connect to RabbitMQ at {RABBIT_HOST}")
    return None

# =========================
# Listener Thread
# =========================
def listen():
    connection = get_connection()
    if not connection:
        return

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=True
    )
    channel.start_consuming()

# =========================
# Standalone Mode
# =========================
def standalone_mode():
    print("=" * 50)
    print("STANDALONE MODE (No RabbitMQ)")
    print("=" * 50)

    display_history()

    print("Messages will not be sent to any other container.\n")

    try:
        while True:
            text = input("Type message (standalone): ")
            if text.strip():
                log = f"Sent by {USER_NAME} (standalone): {text}"
                print(log)
                save_to_history(log)
    except KeyboardInterrupt:
        print("\nExiting standalone mode...")

# =========================
# Main Execution
# =========================
if STANDALONE_MODE:
    standalone_mode()
    sys.exit(0)

display_history()

# Start listener in background
threading.Thread(target=listen, daemon=True).start()

print(f"--- Chat Started ({USER_NAME} connecting to {RABBIT_HOST}) ---")

connection = get_connection()
if not connection:
    print("\nFalling back to standalone mode...")
    standalone_mode()
    sys.exit(1)

channel = connection.channel()
channel.queue_declare(queue=TARGET_QUEUE)

try:
    while True:
        text = input("Type message: ")
        if text.strip():
            payload = {
                "sender": USER_NAME,
                "message": text
            }

            channel.basic_publish(
                exchange='',
                routing_key=TARGET_QUEUE,
                body=json.dumps(payload)
            )

            log = f"Sent by {USER_NAME}: {text}"
            print(log)
            save_to_history(log)

except KeyboardInterrupt:
    connection.close()
    print("\nChat ended.")
