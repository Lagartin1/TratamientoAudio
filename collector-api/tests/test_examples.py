def test_list_examples(client):
    response = client.get("/api/examples")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert len(response.json["data"]) == 2


def test_get_missing_example_returns_404(client):
    response = client.get("/api/examples/999")

    assert response.status_code == 404
    assert response.json["ok"] is False
    assert response.json["message"] == "Example 999 not found"


def test_validate_payload_requires_name(client):
    response = client.post("/api/examples/validate", json={})

    assert response.status_code == 400
    assert response.json["ok"] is False
    assert response.json["errors"]["name"] == ["This field is required"]
