from flask import Flask

from config import get_config
from webiste.app.commands import register_commands
from webiste.app.exceptions.handlers import register_error_handlers
from webiste.app.extensions import cors, db
from webiste.app.http.middleware import register_middlewares
from webiste.routes import register_routes


def create_app(config_name=None):
    app = Flask(__name__)

    # Endpoint para ping-db (debe ir después de crear app)
    @app.route("/ping-db", methods=["GET"])
    def ping_db():
        from sqlalchemy import text
        info = {}
        try:
            with db.engine.connect() as conn:
                schema = conn.execute(text("SELECT current_schema()" )).scalar()
                db_name = conn.execute(text("SELECT current_database()" )).scalar()
                user = conn.execute(text("SELECT current_user")).scalar()
                version = conn.execute(text("SELECT version()"))
                version = version.scalar() if version else None
                info = {
                    "status": "ok",
                    "database": db_name,
                    "user": user,
                    "schema": schema,
                    "postgres_version": version,
                    "supabase_url": app.config.get("SUPABASE_DB_URL") or app.config.get("DATABASE_URL"),
                }
        except Exception as e:
            import traceback
            info = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        return info
    app.config.from_object(get_config(config_name))

    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    register_middlewares(app)
    register_error_handlers(app)
    register_routes(app)
    register_commands(app)
    # Ruta raíz de saludo
    @app.route("/")
    def hello():
        return {"message": "¡Hola! El servidor está funcionando correctamente."}

    return app
