import json
import logging
import os
import signal
import sys
import tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from models.audio_crud import (
    create_log_sample,
    get_audio_by_id,
    replace_bird_detections,
    update_audio_analysis,
)

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "audio_tasks")
BLOCK_TIMEOUT_SECONDS = int(os.getenv("REDIS_BLOCK_TIMEOUT_SECONDS", "5"))

shutdown_requested = False
SRC_DIR = Path(__file__).resolve().parent
UTILS_DIR = SRC_DIR / "utils"


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


def load_class_from_file(file_path: Path, class_name: str) -> type:
    spec = spec_from_file_location(file_path.stem.replace("-", "_"), file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar modulo desde {file_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def get_sound_classifier_class() -> type:
    return load_class_from_file(
        UTILS_DIR / "sound-especs-clasify.py",
        "SoundSpecsClassifier",
    )


def get_bird_classifier_class() -> type:
    return load_class_from_file(
        UTILS_DIR / "bird-clasify.py",
        "ClassifyBirds",
    )


def write_audio_file(audio: dict[str, Any]) -> Path:
    audio_file = audio.get("audio_file")
    if audio_file is None:
        raise ValueError(f"El audio {audio.get('id')} no tiene audio_file")

    if isinstance(audio_file, memoryview):
        audio_file = audio_file.tobytes()
    else:
        audio_file = bytes(audio_file)

    file_extension = audio.get("file_extension") or "wav"
    suffix = file_extension if file_extension.startswith(".") else f".{file_extension}"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(audio_file)
        return Path(temp_file.name)


def safe_create_log_sample(**kwargs: Any) -> None:
    try:
        create_log_sample(**kwargs)
    except Exception:
        logging.exception("Failed to create log_sample")


def process_message(message: Any) -> None:
    print_status(f"processing message: {message}")
    logging.info("Processing message: %s", message)

    if not isinstance(message, dict):
        raise ValueError(f"Mensaje invalido: {message}")

    audio_id = message.get("audio_id")
    if not audio_id:
        raise ValueError(f"Mensaje sin audio_id: {message}")

    safe_create_log_sample(
        id_audio=audio_id,
        track=1,
        payload={"event": "job_received", "message": message},
    )

    audio = get_audio_by_id(audio_id)
    if audio is None:
        error = f"No existe audio con id {audio_id}"
        safe_create_log_sample(
            id_audio=audio_id,
            track=2,
            payload={"event": "audio_not_found"},
            error=error,
        )
        raise LookupError(error)

    temp_audio_path = write_audio_file(audio)

    try:
        SoundSpecsClassifier = get_sound_classifier_class()
        sound_results = SoundSpecsClassifier(str(temp_audio_path)).classify()
        ClassifyBirds = get_bird_classifier_class()
        bird_classifier = ClassifyBirds(str(temp_audio_path))
        bird_classifier.classify()
        bird_results = bird_classifier.get_results()
        bird_names = [
            result.get("common_name") or result.get("species")
            for result in bird_results
            if result.get("common_name") or result.get("species")
        ]

        update_audio_analysis(
            audio_id,
            audio_category=sound_results["noise_type"],
            decibels=sound_results["decibels"],
            duration=sound_results["duration"],
            avg_frequency=sound_results["avg_frequency"],
        )
        replace_bird_detections(audio_id, bird_names)

        safe_create_log_sample(
            id_audio=audio_id,
            id_device=audio.get("id_device"),
            track=3,
            payload={
                "event": "audio_processed",
                "sound": sound_results,
                "birds": bird_results,
            },
        )
    except Exception as exc:
        safe_create_log_sample(
            id_audio=audio_id,
            id_device=audio.get("id_device"),
            track=4,
            payload={"event": "audio_processing_failed"},
            error=str(exc),
        )
        raise
    finally:
        temp_audio_path.unlink(missing_ok=True)


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
