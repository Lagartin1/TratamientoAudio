from datetime import datetime, timezone

from webiste.app.extensions import db

from .types import GUID


class Login(db.Model):
    __tablename__ = "LOGIN"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    token = db.Column(db.String, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    time = db.Column(db.String)
    id_user = db.Column(GUID(), db.ForeignKey("USER.id"), nullable=False)

    user = db.relationship("User", back_populates="logins")

    def to_dict(self):
        return {
            "id": self.id,
            "token": self.token,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "time": self.time,
            "id_user": str(self.id_user),
        }
