from webiste.app.extensions import db

from .types import GUID


class Bird(db.Model):
    __tablename__ = "BIRDS"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    audio_id = db.Column(GUID(), db.ForeignKey("AUDIOS.id"), nullable=False)
    name = db.Column(db.String, nullable=False)

    audio = db.relationship("Audio", back_populates="birds")

    def to_dict(self):
        return {
            "id": self.id,
            "audio_id": str(self.audio_id),
            "name": self.name,
        }
