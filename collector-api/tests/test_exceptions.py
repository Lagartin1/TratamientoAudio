def test_unexpected_exception_returns_500(client):
    response = client.get("/api/examples/force-error")

    assert response.status_code == 500
    assert response.json["ok"] is False
    assert response.json["message"] == "Internal server error"
