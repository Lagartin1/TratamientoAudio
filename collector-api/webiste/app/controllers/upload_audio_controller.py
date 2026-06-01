from flask import request
from webiste.app.extensions import db
from webiste.app.helpers.responses import error_response, success_response
from webiste.app.models.audio import Audio
from webiste.app.models.device import Device
from webiste.app.models.location import Location
from webiste.app.models.user import User
import os

# Endpoint: /api/upload-audio

def upload_audio():
    # archivo
    audio_file = request.files.get('audio')
    if not audio_file:
        return error_response("audio file is required in form 'audio'", 400)

    # latitude/longitude opcionales pero recomendadas
    try:
        latitude = request.form.get('latitude')
        latitude = float(latitude) if latitude is not None and latitude != '' else None
    except ValueError:
        return error_response("latitude must be a float", 400)

    try:
        longitude = request.form.get('longitude')
        longitude = float(longitude) if longitude is not None and longitude != '' else None
    except ValueError:
        return error_response("longitude must be a float", 400)

    # id_user/model/os_version opcionales (frontend puede no enviarlos)
    id_user = request.form.get('id_user')
    model = request.form.get('model') or "unknown"
    os_version = request.form.get('os_version') or "unknown"

    # Si no viene id_user, usar el primer usuario existente como fallback
    user = None
    if id_user:
        user = User.query.filter_by(id=id_user).first()
        if not user:
            return error_response("User not found for provided id_user", 404)
    else:
        user = User.query.first()
        if not user:
            return error_response("No users exist in the system. Provide id_user or create a user first.", 422)
        id_user = user.id

    # Crear location solo si vienen coordenadas
    location = None
    if latitude is not None and longitude is not None:
        location = Location(latitude=latitude, longitude=longitude)
        db.session.add(location)
        db.session.commit()

    # Crear device vinculado al usuario (modelo y os_version pueden ser 'unknown')
    device = Device(id_user=id_user, model=model, os_version=os_version)
    db.session.add(device)
    db.session.commit()

    # Guardar el audio en binario (LargeBinary -> bytea)
    audio_data = audio_file.read()
    file_extension = os.path.splitext(audio_file.filename)[-1].replace('.', '')
    audio = Audio(
        id_device=device.id,
        audio_file=audio_data,
        file_extension=file_extension or "webm",
        location=location.id if location else None,
    )
    db.session.add(audio)
    db.session.commit()

    return success_response({
        "audio_id": str(audio.id),
        "device_id": str(device.id),
        "location_id": str(location.id) if location else None,
        "filename": audio_file.filename,
        "size_bytes": len(audio_data)
    }, "Audio uploaded successfully", 201)
