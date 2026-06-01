class ApiException(Exception):
    status_code = 400
    message = "Application error"

    def __init__(self, message=None, status_code=None, errors=None):
        self.message = message or self.message
        self.status_code = status_code or self.status_code
        self.errors = errors
        super().__init__(self.message)


class BadRequestException(ApiException):
    status_code = 400
    message = "Bad request"


class NotFoundException(ApiException):
    status_code = 404
    message = "Resource not found"


class DatabaseConnectionException(ApiException):
    status_code = 503
    message = "Database connection failed"
