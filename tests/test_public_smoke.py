def test_home_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hoist the Mainsail" in response.data
