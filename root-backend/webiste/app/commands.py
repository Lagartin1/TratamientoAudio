import io
import struct
import wave
from pathlib import Path

import click
from flask.cli import with_appcontext

from webiste.app.extensions import db


def _silent_wav(duration_seconds: float = 2.0, sample_rate: int = 44100) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00\x00" * int(sample_rate * duration_seconds))
    return buf.getvalue()


@click.command("init-db")
@with_appcontext
def init_db_command():
    from webiste.app import models  # noqa: F401

    db.create_all()
    click.echo("Database tables created.")


@click.command("init-sql")
@with_appcontext
def init_sql_command():
    if db.engine.dialect.name != "postgresql":
        raise click.ClickException("init-sql solo funciona con PostgreSQL.")

    schema_path = Path(__file__).resolve().parent.parent.parent / "sql" / "init_schema.sql"
    statements = [
        s.strip()
        for s in schema_path.read_text(encoding="utf-8").split(";")
        if s.strip()
    ]

    with db.engine.begin() as conn:
        for stmt in statements:
            conn.exec_driver_sql(stmt)

    click.echo(f"Schema inicializado desde {schema_path}.")


@click.command("seed-db")
@with_appcontext
def seed_db_command():
    from webiste.app.models.audio import Audio
    from webiste.app.models.bird import Bird
    from webiste.app.models.device import Device
    from webiste.app.models.location import Location
    from webiste.app.models.user import User

    click.echo("Recreando tablas...")
    db.drop_all()
    db.create_all()

    # Usuario de prueba
    user = User(name="Admin SoundColab", username="admin", password="admin123", role="admin")
    db.session.add(user)
    db.session.flush()

    # Ubicaciones en el campus Miraflores (Valdivia, Chile)
    locations_data = [
        (-39.8196, -73.2452, "despejado"),
        (-39.8201, -73.2458, "nublado"),
        (-39.8189, -73.2441, "lluvia leve"),
    ]
    locations = []
    for lat, lon, weather in locations_data:
        loc = Location(latitude=lat, longitude=lon, weather=weather)
        db.session.add(loc)
        locations.append(loc)
    db.session.flush()

    # Dispositivo asociado al usuario
    device = Device(id_user=user.id, model="Pixel 7", os_version="Android 14")
    db.session.add(device)
    db.session.flush()

    # Audios con archivo WAV silencioso de prueba
    audio_seed = [
        ("bird",   45.2, 3.1, 4200.0, locations[0]),
        ("bird",   38.7, 2.8, 3800.0, locations[0]),
        ("traffic",72.4, 5.0, 1200.0, locations[1]),
        ("silence",22.1, 4.0,  800.0, locations[2]),
        ("bird",   41.0, 2.5, 5100.0, locations[2]),
    ]
    wav_bytes = _silent_wav()
    audios = []
    for category, db_val, duration, freq, loc in audio_seed:
        audio = Audio(
            id_device=device.id,
            audio_file=wav_bytes,
            audio_category=category,
            decibels=db_val,
            duration=duration,
            avg_frecuency=freq,
            file_extension="wav",
            location=loc.id,
        )
        db.session.add(audio)
        audios.append(audio)
    db.session.flush()

    # Aves detectadas en los audios de categoría "bird"
    bird_detections = [
        (audios[0], ["Queltehue", "Zorzal de Mara"]),
        (audios[1], ["Picaflor de Juan Fernandez"]),
        (audios[4], ["Queltehue", "Chincol"]),
    ]
    for audio, names in bird_detections:
        for name in names:
            db.session.add(Bird(audio_id=audio.id, name=name))

    db.session.commit()
    click.echo("Seed completado:")
    click.echo(f"  - 1 usuario  (username: admin / password: admin123)")
    click.echo(f"  - 3 ubicaciones en Valdivia")
    click.echo(f"  - 1 dispositivo")
    click.echo(f"  - {len(audios)} audios ({sum(1 for a in audio_seed if a[0]=='bird')} bird, 1 traffic, 1 silence)")
    click.echo(f"  - 4 detecciones de aves")


def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_sql_command)
    app.cli.add_command(seed_db_command)
