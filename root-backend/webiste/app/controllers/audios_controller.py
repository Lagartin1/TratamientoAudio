import base64

from flask import request
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload, defer

from webiste.app.extensions import db
from webiste.app.helpers.responses import error_response, success_response
from webiste.app.models.audio import Audio


def _summary(audio: Audio) -> dict:
    loc = audio.location_ref
    return {
        "audio_id": str(audio.id),
        "audio_category": audio.audio_category,
        "decibels": audio.decibels,
        "duration": audio.duration,
        "avg_frecuency": audio.avg_frecuency,
        "latitud": loc.latitude if loc else None,
        "longitud": loc.longitude if loc else None,
        "weather": loc.weather if loc else None,
        "bird_name": [b.name for b in audio.birds][0] if audio.birds != [] else None,
    }


def list_audios():
    category = request.args.get("category")
    
    stmt = select(Audio).options(
        defer(Audio.audio_file),
        selectinload(Audio.birds),
        joinedload(Audio.location_ref),
    )
    
    if category:
        stmt = stmt.where(Audio.audio_category == category)
        
    audios = db.session.execute(stmt).scalars().all()
    return success_response([_summary(a) for a in audios])


def get_audio(audio_id: str):
    # Usar options en db.session.get para cargar las relaciones
    audio = db.session.get(
        Audio, 
        audio_id, 
        options=[selectinload(Audio.birds), joinedload(Audio.location_ref)]
    )
    
    if audio is None:
        return error_response("Audio no encontrado", 404)

    loc = audio.location_ref
    birds = [b.name for b in audio.birds]

    audio_b64 = None
    if audio.audio_file:
        audio_b64 = base64.b64encode(bytes(audio.audio_file)).decode("utf-8")

    return success_response({
        "audio_id": str(audio.id),
        "audio": audio_b64,
        "file_extension": audio.file_extension,
        "audio_category": audio.audio_category,
        "decibels": audio.decibels,
        "duration": audio.duration,
        "avg_frecuency": audio.avg_frecuency,
        "latitud": loc.latitude if loc else None,
        "longitud": loc.longitude if loc else None,
        "weather": loc.weather if loc else None,
        "birds": birds,
    })