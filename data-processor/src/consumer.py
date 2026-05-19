import json
import logging
import os
import signal
import sys
from typing import Any

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "audio_tasks")
BLOCK_TIMEOUT_SECONDS = int(os.getenv("REDIS_BLOCK_TIMEOUT_SECONDS", "5"))

shutdown_requested = False


def print_status(message: str) -> None:
    print(f"[consumer] {message}", flush=True)


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )


def request_shutdown(signum: int, _frame: Any) -> None:
    global shutdown_requested
    print_status(f"shutdown signal received: {signum}")
    logging.info("Shutdown signal received: %s", signum)
    shutdown_requested = True


def parse_message(raw_message: bytes) -> Any:
    message = raw_message.decode("utf-8")

    try:
        return json.loads(message)
    except json.JSONDecodeError:
        return message


def process_message(message: Any) -> None:
    print_status(f"processing message: {message}")
    logging.info("Processing message: %s", message)
    # Add audio processing logic here.


def create_redis_client(redis_url: str = REDIS_URL) -> redis.Redis:
    return redis.Redis.from_url(redis_url, decode_responses=False)


def consume(
    client: redis.Redis | None = None,
    queue_name: str = QUEUE_NAME,
    block_timeout_seconds: int = BLOCK_TIMEOUT_SECONDS,
    max_messages: int | None = None,
) -> int:
    print_status(f"connecting to Redis: {REDIS_URL}")
    client = client or create_redis_client()
    client.ping()
    processed_messages = 0

    print_status(f"consumer launched and listening on queue: {queue_name}")
    logging.info("Listening for messages on Redis queue '%s'", queue_name)

    while not shutdown_requested:
        if max_messages is not None and processed_messages >= max_messages:
            break

        item = client.blpop(queue_name, timeout=block_timeout_seconds)

        if item is None:
            print_status(f"waiting for messages on '{queue_name}'...")
            continue

        _queue, raw_message = item
        message = parse_message(raw_message)
        print_status(f"message received from '{queue_name}': {message}")

        try:
            process_message(message)
            processed_messages += 1
        except Exception:
            logging.exception("Failed to process message: %s", message)

    return processed_messages


def main() -> int:
    print_status("starting consumer.py")
    configure_logging()
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    try:
        consume()
    except redis.RedisError:
        print_status("Redis connection error")
        logging.exception("Redis connection error")
        return 1

    print_status("consumer stopped")
    logging.info("Consumer stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
