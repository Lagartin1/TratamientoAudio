from werkzeug.exceptions import HTTPException

from webiste.app.exceptions.api_exceptions import ApiException
from webiste.app.helpers.responses import error_response


def register_error_handlers(app):
    @app.errorhandler(ApiException)
    def handle_api_exception(error):
        return error_response(error.message, error.status_code, error.errors)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return error_response(error.description, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.exception(error)
        return error_response("Internal server error", 500)
