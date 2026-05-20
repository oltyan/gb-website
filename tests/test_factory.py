def test_app_factory_returns_flask_app(app):
    assert app.name == "app"
    assert app.config["TESTING"] is True


def test_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
