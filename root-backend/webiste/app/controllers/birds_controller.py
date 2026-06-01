from flask import request
from sqlalchemy import select

from webiste.app.extensions import db
from webiste.app.helpers.responses import success_response
from webiste.app.models.bird import Bird


def list_birds():
    audio_id = request.args.get("audio_id")
    name = request.args.get("name")

    stmt = select(Bird)
    if audio_id:
        stmt = stmt.where(Bird.audio_id == audio_id)
    if name:
        stmt = stmt.where(Bird.name.ilike(f"%{name}%"))

    birds = db.session.execute(stmt.order_by(Bird.id)).scalars().all()
    return success_response([b.to_dict() for b in birds])
