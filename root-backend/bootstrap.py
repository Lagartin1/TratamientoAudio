from flask import Flask

from config import get_config
from webiste.app.commands import register_commands
from webiste.app.exceptions.handlers import register_error_handlers
from webiste.app.extensions import cors, db
from webiste.app.http.middleware import register_middlewares
from webiste.routes import register_routes


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    db.init_app(app)


    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    print(app.config["CORS_ORIGINS"])

    register_middlewares(app)
    register_error_handlers(app)
    register_routes(app)
    register_commands(app)

    return app
