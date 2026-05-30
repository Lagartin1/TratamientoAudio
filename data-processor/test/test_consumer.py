import uuid
from pathlib import Path

import pytest
import redis
from sqlalchemy import text

import consumer
from models.audio_crud import get_table_name
from models.postgres_connection import db_session

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


def _postgres_available() -> tuple[bool, str | None]:
    try:
        with db_session() as session:
            session.execute(text("select 1"))
        return True, None
    except Exception as exc:
        return False, str(exc)


def _insert_audio_fixture(audio_path: Path) -> dict[str, str]:
    audio_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    device_id = str(uuid.uuid4())

    with db_session() as session:
        audios_table = get_table_name(session, "audios")
        user_table = get_table_name(session, "user")
        devices_table = get_table_name(session, "devices")
        session.execute(
            text(
                f"""
                insert into {user_table} (id, name, username, password, role)
                values (:id, :name, :username, :password, :role)
                """
            ),
            {
                "id": user_id,
                "name": "Integration Test",
                "username": f"integration-{user_id}",
                "password": "test-only",
                "role": "test",
            },
        )
        session.execute(
            text(
                f"""
                insert into {devices_table} (id, id_user, model, os_version)
                values (:id, :id_user, :model, :os_version)
                """
            ),
            {
                "id": device_id,
                "id_user": user_id,
                "model": "pytest",
                "os_version": "test",
            },
        )
        session.execute(
            text(
                f"""
                insert into {audios_table} (
                    id,
                    id_device,
                    audio_file,
                    file_extension
                )
                values (
                    :id,
                    :id_device,
                    :audio_file,
                    :file_extension
                )
                """
            ),
            {
                "id": audio_id,
                "id_device": device_id,
                "audio_file": audio_path.read_bytes(),
                "file_extension": "wav",
            },
        )

    return {"audio_id": audio_id, "user_id": user_id, "device_id": device_id}


def _delete_audio_fixture(ids: dict[str, str]) -> None:
    with db_session() as session:
        audios_table = get_table_name(session, "audios")
        birds_table = get_table_name(session, "birds")
        log_sample_table = get_table_name(session, "log_sample")
        user_table = get_table_name(session, "user")
        devices_table = get_table_name(session, "devices")
        session.execute(
            text(f"delete from {birds_table} where audio_id = :audio_id"),
            {"audio_id": ids["audio_id"]},
        )
        session.execute(
            text(f"delete from {log_sample_table} where id_audio = :audio_id"),
            {"audio_id": ids["audio_id"]},
        )
        session.execute(
            text(f"delete from {audios_table} where id = :audio_id"),
            {"audio_id": ids["audio_id"]},
        )
        session.execute(
            text(f"delete from {devices_table} where id = :device_id"),
            {"device_id": ids["device_id"]},
        )
        session.execute(
            text(f"delete from {user_table} where id = :user_id"),
            {"user_id": ids["user_id"]},
        )


def test_queltehue_audio_is_persisted_queued_consumed_and_processed():
    redis_connection = redis_client()
    try:
        redis_connection.ping()
    except redis.RedisError as exc:
        pytest.skip(f"Redis is not available: {exc}")

    db_is_available, db_error = _postgres_available()
    if not db_is_available:
        pytest.skip(f"Postgres is not available: {db_error}")

    audio_path = Path(__file__).with_name("queltehue.wav")
    if not audio_path.exists():
        pytest.skip(f"Audio fixture is missing: {audio_path}")

    queue_name = f"test_audio_tasks:{uuid.uuid4()}"
    fixture_ids = _insert_audio_fixture(audio_path)

    try:
        redis_connection.delete(queue_name)
        redis_connection.lpush(
            queue_name,
            f'{{"audio_id":"{fixture_ids["audio_id"]}"}}'.encode("utf-8"),
        )

        consumer.shutdown_requested = False
        processed_count = consumer.consume(
            client=redis_connection,
            queue_name=queue_name,
            block_timeout_seconds=1,
            max_messages=1,
        )

        assert processed_count == 1
        assert redis_connection.llen(queue_name) == 0

        with db_session() as session:
            audios_table = get_table_name(session, "audios")
            log_sample_table = get_table_name(session, "log_sample")
            processed_audio = session.execute(
                text(
                    f"""
                    select audio_category, decibels, duration, avg_frecuency
                    from {audios_table}
                    where id = :audio_id
                    """
                ),
                {"audio_id": fixture_ids["audio_id"]},
            ).mappings().one()
            processed_logs = session.execute(
                text(
                    f"""
                    select payload, error
                    from {log_sample_table}
                    where id_audio = :audio_id
                    order by timestamp asc
                    """
                ),
                {"audio_id": fixture_ids["audio_id"]},
            ).mappings().all()

        assert processed_audio["audio_category"]
        assert processed_audio["decibels"] is not None
        assert processed_audio["duration"] > 0
        assert processed_audio["avg_frecuency"] > 0
        assert any(
            log["payload"] and "audio_processed" in log["payload"] and not log["error"]
            for log in processed_logs
        )
    finally:
        redis_connection.delete(queue_name)
        _delete_audio_fixture(fixture_ids)
