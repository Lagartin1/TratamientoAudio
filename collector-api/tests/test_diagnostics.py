def test_ping_returns_pong(client):
    response = client.get("/api/ping")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["message"] == "pong"
    assert response.json["data"]["pong"] is True


def test_database_ping_returns_connection_status(client):
    response = client.get("/api/db/ping")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["data"]["connected"] is True
