import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest
import redis
from sqlalchemy import text

from models.audio_crud import get_table_name
from models.postgres_connection import db_session


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = PROJECT_DIR / "src" / ".env"


def _run(command: list[str], timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def _docker_available() -> tuple[bool, str | None]:
    if shutil.which("docker") is None:
        return False, "docker is not installed or is not in PATH"

    result = _run(["docker", "info"], timeout=30)
    if result.returncode != 0:
        return False, result.stdout

    return True, None


def _docker_env_file() -> Path:
    env_file = os.getenv("DOCKER_ENV_FILE")
    if not env_file:
        return DEFAULT_ENV_FILE

    env_path = Path(env_file)
    if env_path.is_absolute():
        return env_path

    return PROJECT_DIR / env_path


def _load_env_value(key: str, default: str) -> str:
    env_value = os.getenv(key)
    if env_value:
        return env_value

    env_file = _docker_env_file()
    if not env_file.exists():
        return default

    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        env_key, value = line.split("=", 1)
        if env_key.strip() == key:
            return value.strip().strip('"').strip("'")

    return default


def _require_docker_tests_enabled() -> None:
    if os.getenv("RUN_DOCKER_TESTS") != "1":
        pytest.skip("Set RUN_DOCKER_TESTS=1 in test/.env to run Docker tests")

    docker_is_available, docker_error = _docker_available()
    if not docker_is_available:
        pytest.skip(f"Docker is not available: {docker_error}")


def _require_running_container() -> str:
    container_name = os.getenv("CONTAINER_NAME", "data-processor")
    inspect_result = _run(
        [
            "docker",
            "inspect",
            "-f",
            "{{.State.Running}}",
            container_name,
        ],
        timeout=30,
    )
    if inspect_result.returncode != 0 or "true" not in inspect_result.stdout:
        pytest.skip(f"Docker container is not running: {container_name}")

    return container_name


def _postgres_available() -> tuple[bool, str | None]:
    try:
        with db_session() as session:
            session.execute(text("select 1"))
        return True, None
    except Exception as exc:
        return False, str(exc)


def _redis_client() -> redis.Redis:
    redis_url = _load_env_value("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(redis_url, decode_responses=False)


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
                "name": "Docker Integration Test",
                "username": f"docker-integration-{user_id}",
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
                "model": "pytest-docker",
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


def _processed_audio(audio_id: str) -> tuple[dict | None, list[dict]]:
    with db_session() as session:
        audios_table = get_table_name(session, "audios")
        log_sample_table = get_table_name(session, "log_sample")
        audio = session.execute(
            text(
                f"""
                select audio_category, decibels, duration, avg_frecuency
                from {audios_table}
                where id = :audio_id
                """
            ),
            {"audio_id": audio_id},
        ).mappings().one_or_none()
        logs = session.execute(
            text(
                f"""
                select payload, error
                from {log_sample_table}
                where id_audio = :audio_id
                order by timestamp asc
                """
            ),
            {"audio_id": audio_id},
        ).mappings().all()

    return (dict(audio) if audio else None, [dict(log) for log in logs])


def test_docker_image_builds_and_can_import_consumer():
    _require_docker_tests_enabled()

    image_name = f"data-processor:test-{uuid.uuid4()}"
    expected_queue_name = _load_env_value("REDIS_QUEUE_NAME", "audio_tasks")
    docker_env_file = _docker_env_file()
    docker_network_mode = os.getenv("DOCKER_NETWORK_MODE", "host")

    if not docker_env_file.exists():
        pytest.skip(f"Docker env file is missing: {docker_env_file}")

    try:
        build_result = _run(["docker", "build", "-t", image_name, "."])
        assert build_result.returncode == 0, build_result.stdout

        command = [
            "docker",
            "run",
            "--rm",
            "--env-file",
            str(docker_env_file),
            "--network",
            docker_network_mode,
            "--entrypoint",
            "python",
            image_name,
            "-c",
            (
                "import shutil; "
                "import consumer; "
                "assert shutil.which('ffmpeg'), 'ffmpeg is missing'; "
                "print(f'consumer queue={consumer.QUEUE_NAME}')"
            ),
        ]
        run_result = _run(command, timeout=120)
        assert run_result.returncode == 0, run_result.stdout
        assert f"consumer queue={expected_queue_name}" in run_result.stdout
    finally:
        _run(["docker", "rmi", "-f", image_name], timeout=120)


def test_running_docker_container_consumes_queue_and_processes_audio():
    _require_docker_tests_enabled()
    container_name = _require_running_container()

    redis_connection = _redis_client()
    try:
        redis_connection.ping()
    except redis.RedisError as exc:
        pytest.skip(f"Redis is not available: {exc}")

    db_is_available, db_error = _postgres_available()
    if not db_is_available:
        pytest.skip(f"Postgres is not available: {db_error}")

    audio_path = PROJECT_DIR / "test" / "queltehue.wav"
    if not audio_path.exists():
        pytest.skip(f"Audio fixture is missing: {audio_path}")

    queue_name = _load_env_value("REDIS_QUEUE_NAME", "audio_tasks")
    fixture_ids = _insert_audio_fixture(audio_path)
    payload = f'{{"audio_id":"{fixture_ids["audio_id"]}"}}'.encode("utf-8")

    try:
        exec_result = _run(
            [
                "docker",
                "exec",
                container_name,
                "python",
                "-c",
                (
                    "import consumer; "
                    "client = consumer.create_redis_client(); "
                    "assert client.ping() is True; "
                    "print(f'redis ok queue={consumer.QUEUE_NAME}')"
                ),
            ],
            timeout=120,
        )
        assert exec_result.returncode == 0, exec_result.stdout
        assert f"redis ok queue={queue_name}" in exec_result.stdout

        redis_connection.lpush(queue_name, payload)

        e2e_timeout = int(os.getenv("DOCKER_E2E_TIMEOUT_SECONDS", "240"))
        deadline = time.monotonic() + e2e_timeout
        processed_audio = None
        processed_logs = []
        while time.monotonic() < deadline:
            processed_audio, processed_logs = _processed_audio(fixture_ids["audio_id"])
            if processed_audio and any(
                log["payload"]
                and "audio_processed" in log["payload"]
                and not log["error"]
                for log in processed_logs
            ):
                break
            if any(log["error"] for log in processed_logs):
                break
            time.sleep(2)

        assert processed_audio is not None
        assert processed_audio["audio_category"]
        assert processed_audio["decibels"] is not None
        assert processed_audio["duration"] > 0
        assert processed_audio["avg_frecuency"] > 0
        assert any(
            log["payload"] and "audio_processed" in log["payload"] and not log["error"]
            for log in processed_logs
        ), processed_logs
    finally:
        redis_connection.lrem(queue_name, 0, payload)
        _delete_audio_fixture(fixture_ids)


def test_running_docker_container_can_reach_redis():
    _require_docker_tests_enabled()
    container_name = _require_running_container()

    exec_result = _run(
        [
            "docker",
            "exec",
            container_name,
            "python",
            "-c",
            (
                "import consumer; "
                "client = consumer.create_redis_client(); "
                "assert client.ping() is True; "
                "print(f'redis ok queue={consumer.QUEUE_NAME}')"
            ),
        ],
        timeout=120,
    )

    assert exec_result.returncode == 0, exec_result.stdout
    assert "redis ok queue=" in exec_result.stdout
