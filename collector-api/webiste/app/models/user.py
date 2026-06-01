from webiste.app.extensions import db

from .types import GUID, uuid_default


class User(db.Model):
    __tablename__ = "USER"

    id = db.Column(GUID(), primary_key=True, default=uuid_default)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False, index=True)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)

    devices = db.relationship("Device", back_populates="user")
    logins = db.relationship("Login", back_populates="user")
    logs = db.relationship("LogSample", back_populates="user")

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "username": self.username,
            "role": self.role,
        }
