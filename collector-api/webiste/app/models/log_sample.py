from datetime import datetime, timezone

from webiste.app.extensions import db

from .types import GUID, uuid_default


class LogSample(db.Model):
    __tablename__ = "log_sample"

    id = db.Column(GUID(), primary_key=True, default=uuid_default)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    id_audio = db.Column(GUID(), db.ForeignKey("AUDIOS.id"))
    id_user = db.Column(GUID(), db.ForeignKey("USER.id"))
    id_device = db.Column(GUID(), db.ForeignKey("DEVICES.id"))
    track = db.Column(db.SmallInteger)
    payload = db.Column(db.Text)
    error = db.Column(db.Text)

    audio = db.relationship("Audio", back_populates="logs")
    user = db.relationship("User", back_populates="logs")
    device = db.relationship("Device", back_populates="logs")

    def to_dict(self):
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "id_audio": str(self.id_audio) if self.id_audio else None,
            "id_user": str(self.id_user) if self.id_user else None,
            "id_device": str(self.id_device) if self.id_device else None,
            "track": self.track,
            "payload": self.payload,
            "error": self.error,
        }
