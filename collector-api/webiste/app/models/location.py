from webiste.app.extensions import db

from .types import GUID, uuid_default


class Location(db.Model):
    __tablename__ = "LOCATIONS"

    id = db.Column(GUID(), primary_key=True, default=uuid_default)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    weather = db.Column(db.Text)

    audios = db.relationship("Audio", back_populates="location_ref")

    def to_dict(self):
        return {
            "id": str(self.id),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "weather": self.weather,
        }
