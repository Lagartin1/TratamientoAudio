from flask import request

from webiste.app.exceptions.api_exceptions import BadRequestException, NotFoundException
from webiste.app.helpers.responses import success_response


EXAMPLE_ITEMS = {
    1: {"id": 1, "name": "Primer ejemplo", "status": "active"},
    2: {"id": 2, "name": "Segundo ejemplo", "status": "inactive"},
}


def list_examples():
    status = request.args.get("status")
    items = list(EXAMPLE_ITEMS.values())

    if status:
        items = [item for item in items if item["status"] == status]

    return success_response(items)


def get_example(example_id):
    item = EXAMPLE_ITEMS.get(example_id)
    if not item:
        raise NotFoundException(f"Example {example_id} not found")

    return success_response(item)


def validate_payload_example():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")

    if not name:
        raise BadRequestException(
            "name is required",
            errors={"name": ["This field is required"]},
        )

    return success_response(
        {
            "name": name,
            "received": payload,
        },
        "Payload valid",
    )


def forced_exception_example():
    raise RuntimeError("Forced exception for testing")
