from webiste.app.extensions import db

from .types import GUID, uuid_default


class Device(db.Model):
    __tablename__ = "DEVICES"

    id = db.Column(GUID(), primary_key=True, default=uuid_default)
    id_user = db.Column(GUID(), db.ForeignKey("USER.id"), nullable=False)
    model = db.Column(db.String)
    os_version = db.Column(db.String)

    user = db.relationship("User", back_populates="devices")
    audios = db.relationship("Audio", back_populates="device")

    def to_dict(self):
        return {
            "id": str(self.id),
            "id_user": str(self.id_user),
            "model": self.model,
            "os_version": self.os_version,
        }
