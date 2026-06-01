from webiste.app.extensions import db

from .types import GUID, uuid_default


class Audio(db.Model):
    __tablename__ = "AUDIOS"

    id = db.Column(GUID(), primary_key=True, default=uuid_default)
    id_device = db.Column(GUID(), db.ForeignKey("DEVICES.id"), nullable=False)
    audio_file = db.Column(db.LargeBinary, nullable=False)
    audio_category = db.Column(db.String)
    decibels = db.Column(db.Float)
    duration = db.Column(db.Float)
    avg_frecuency = db.Column(db.Float)
    file_extension = db.Column(db.String, nullable=False)
    location = db.Column(GUID(), db.ForeignKey("LOCATIONS.id"))

    device = db.relationship("Device", back_populates="audios")
    location_ref = db.relationship("Location", back_populates="audios")
    birds = db.relationship("Bird", back_populates="audio")

    def to_dict(self):
        return {
            "id": str(self.id),
            "id_device": str(self.id_device),
            "audio_category": self.audio_category,
            "decibels": self.decibels,
            "duration": self.duration,
            "avg_frecuency": self.avg_frecuency,
            "file_extension": self.file_extension,
            "location": str(self.location) if self.location else None,
            "bird": self.birds,
        }
