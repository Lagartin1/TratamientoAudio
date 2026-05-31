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
    if 'audio' not in request.files:
        return error_response("audio file is required", 400)
    audio_file = request.files['audio']
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    id_user = request.form.get('id_user')
    model = request.form.get('model')
    os_version = request.form.get('os_version')

    if not all([audio_file, latitude, longitude, id_user, model, os_version]):
        return error_response("All fields are required", 400)

    # Verifica que el usuario exista
    user = User.query.filter_by(id=id_user).first()
    if not user:
        return error_response("User not found", 404)

    # Crea la ubicación
    location = Location(latitude=latitude, longitude=longitude)
    db.session.add(location)
    db.session.commit()

    # Crea el dispositivo
    device = Device(id_user=id_user, model=model, os_version=os_version)
    db.session.add(device)
    db.session.commit()

    # Guarda el audio en binario
    audio_data = audio_file.read()
    file_extension = os.path.splitext(audio_file.filename)[-1].replace('.', '')
    audio = Audio(
        id_device=device.id,
        audio_file=audio_data,
        file_extension=file_extension,
        location=location.id
    )
    db.session.add(audio)
    db.session.commit()

    return success_response({
        "audio_id": str(audio.id),
        "device_id": str(device.id),
        "location_id": str(location.id)
    }, "Audio uploaded successfully", 201)
