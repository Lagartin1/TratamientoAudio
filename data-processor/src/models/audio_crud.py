import json
from typing import Any

from sqlalchemy import text

from models.postgres_connection import db_session


TABLE_CANDIDATES = {
    "audios": ('public."AUDIOS"', "public.audios"),
    "birds": ('public."BIRDS"', "public.birds"),
    "devices": ('public."DEVICES"', "public.devices"),
    "locations": ('public."LOCATIONS"', "public.locations"),
    "login": ('public."LOGIN"', "public.login"),
    "user": ('public."USER"', "public.user", 'public."user"'),
    "log_sample": ("public.log_sample", 'public."log_sample"'),
}
_TABLE_CACHE: dict[str, str] = {}


def get_table_name(session, table_key: str) -> str:
    """
    Resuelve el nombre real de tabla para ambientes con nombres legacy en
    mayuscula o esquemas locales en minuscula.
    """
    cached_table = _TABLE_CACHE.get(table_key)
    if cached_table:
        return cached_table

    for table_name in TABLE_CANDIDATES[table_key]:
        exists = session.execute(
            text("select to_regclass(:table_name) is not null"),
            {"table_name": table_name},
        ).scalar_one()
        if exists:
            _TABLE_CACHE[table_key] = table_name
            return table_name

    candidates = ", ".join(TABLE_CANDIDATES[table_key])
    raise RuntimeError(f"No se encontro tabla para {table_key}: {candidates}")


def get_audio_by_id(audio_id: str) -> dict[str, Any] | None:
    """
    Busca un audio por id en la tabla audios.
    """
    with db_session() as session:
        audios_table = get_table_name(session, "audios")
        result = session.execute(
            text(
                f"""
                select
                    id,
                    id_device,
                    audio_file,
                    audio_category,
                    decibels,
                    duration,
                    avg_frecuency,
                    file_extension,
                    location
                from {audios_table}
                where id = :audio_id
                """
            ),
            {"audio_id": audio_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None


def update_audio_analysis(
    audio_id: str,
    *,
    audio_category: str | None = None,
    decibels: float | None = None,
    duration: float | None = None,
    avg_frequency: float | None = None,
    file_extension: str | None = None,
    location: str | None = None,
) -> int:
    """
    Actualiza los campos calculados del audio.
    Solo modifica los valores enviados.
    """
    updates = []
    params: dict[str, Any] = {"audio_id": audio_id}

    fields = {
        "audio_category": audio_category,
        "decibels": decibels,
        "duration": duration,
        "avg_frecuency": avg_frequency,
        "file_extension": file_extension,
        "location": location,
    }

    for column, value in fields.items():
        if value is not None:
            updates.append(f"{column} = :{column}")
            params[column] = value

    if not updates:
        return 0

    with db_session() as session:
        audios_table = get_table_name(session, "audios")
        result = session.execute(
            text(
                f"""
                update {audios_table}
                set {", ".join(updates)}
                where id = :audio_id
                """
            ),
            params,
        )
        return result.rowcount


def create_bird_detection(audio_id: str, name: str) -> int:
    """
    Inserta una especie detectada para un audio.
    """
    with db_session() as session:
        birds_table = get_table_name(session, "birds")
        result = session.execute(
            text(
                f"""
                insert into {birds_table} (audio_id, name)
                values (:audio_id, :name)
                """
            ),
            {"audio_id": audio_id, "name": name},
        )
        return result.rowcount


def delete_bird_detections(audio_id: str) -> int:
    """
    Elimina detecciones previas de aves para un audio.
    """
    with db_session() as session:
        birds_table = get_table_name(session, "birds")
        result = session.execute(
            text(f"delete from {birds_table} where audio_id = :audio_id"),
            {"audio_id": audio_id},
        )
        return result.rowcount


def replace_bird_detections(audio_id: str, names: list[str]) -> int:
    """
    Reemplaza todas las aves detectadas de un audio.
    """
    with db_session() as session:
        birds_table = get_table_name(session, "birds")
        deleted_result = session.execute(
            text(f"delete from {birds_table} where audio_id = :audio_id"),
            {"audio_id": audio_id},
        )

        inserted_count = 0
        for name in names:
            insert_result = session.execute(
                text(
                    f"""
                    insert into {birds_table} (audio_id, name)
                    values (:audio_id, :name)
                    """
                ),
                {"audio_id": audio_id, "name": name},
            )
            inserted_count += insert_result.rowcount

        return deleted_result.rowcount + inserted_count


def list_bird_detections(audio_id: str) -> list[dict[str, Any]]:
    """
    Lista las aves detectadas para un audio.
    """
    with db_session() as session:
        birds_table = get_table_name(session, "birds")
        result = session.execute(
            text(
                f"""
                select id, audio_id, name
                from {birds_table}
                where audio_id = :audio_id
                order by id asc
                """
            ),
            {"audio_id": audio_id},
        )
        return [dict(row) for row in result.mappings().all()]


def create_log_sample(
    *,
    id_audio: str | None = None,
    id_user: str | None = None,
    id_device: str | None = None,
    track: int | None = None,
    payload: dict[str, Any] | str | None = None,
    error: str | None = None,
) -> int:
    """
    Registra un evento del data-processor en log_sample.
    """
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload, ensure_ascii=False)

    with db_session() as session:
        log_sample_table = get_table_name(session, "log_sample")
        result = session.execute(
            text(
                f"""
                insert into {log_sample_table} (
                    timestamp,
                    id_audio,
                    id_user,
                    id_device,
                    track,
                    payload,
                    error
                )
                values (
                    now(),
                    :id_audio,
                    :id_user,
                    :id_device,
                    :track,
                    :payload,
                    :error
                )
                """
            ),
            {
                "id_audio": id_audio,
                "id_user": id_user,
                "id_device": id_device,
                "track": track,
                "payload": payload,
                "error": error,
            },
        )
        return result.rowcount


def list_logs_by_audio_id(audio_id: str) -> list[dict[str, Any]]:
    """
    Lista logs asociados a un audio.
    """
    with db_session() as session:
        log_sample_table = get_table_name(session, "log_sample")
        result = session.execute(
            text(
                f"""
                select
                    id,
                    timestamp,
                    id_audio,
                    id_user,
                    id_device,
                    track,
                    payload,
                    error
                from {log_sample_table}
                where id_audio = :audio_id
                order by timestamp desc
                """
            ),
            {"audio_id": audio_id},
        )
        return [dict(row) for row in result.mappings().all()]
