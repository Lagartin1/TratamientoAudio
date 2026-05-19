import uuid

import pytest
import redis

import consumer

def redis_client() -> redis.Redis:
    return redis.Redis.from_url(consumer.REDIS_URL, decode_responses=False)

def test_consumer_reads_message_from_redis_queue(monkeypatch):
    client = redis_client()

    try:
        client.ping()
    except redis.RedisError as exc:
        pytest.skip(f"Redis is not available: {exc}")

    queue_name = f"test_audio_tasks:{uuid.uuid4()}"
    payload = b'{"audio_id":"123","file_path":"/tmp/audio.wav"}'
    processed_messages = []

    def fake_process_message(message):
        processed_messages.append(message)

    monkeypatch.setattr(consumer, "process_message", fake_process_message)

    try:
        client.delete(queue_name)
        client.lpush(queue_name, payload)

        processed_count = consumer.consume(
            client=client,
            queue_name=queue_name,
            block_timeout_seconds=1,
            max_messages=1,
        )

        assert processed_count == 1
        assert processed_messages == [
            {"audio_id": "123", "file_path": "/tmp/audio.wav"}
        ]
        assert client.llen(queue_name) == 0
    finally:
        client.delete(queue_name)
