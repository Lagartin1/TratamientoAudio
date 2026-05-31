from flask import current_app

from webiste.app.helpers.responses import success_response


def health():
    return success_response(
        {
            "service": "root-backend",
            "environment": current_app.config.get("ENV", "development"),
        }
    )
