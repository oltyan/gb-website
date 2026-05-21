from app.extensions import db
from app.models import Post, Scuttlebutt, SiteSettings
from datetime import datetime


def test_home_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"THE QUARTERDECK" in response.data


def _seed_home(app):
    with app.app_context():
        s = SiteSettings.get_or_create()
        s.hero_quote = "A celtic-pirate fusion band."
        s.hero_image_url = "https://example/x.jpg"
        s.ports_visited = 12
        s.grog_pints = "100+"
        db.session.add(Scuttlebutt(text="Test scuttle", accent="amber", sort_order=0))
        db.session.add(Post(slug="p1", title="Raid at Port Royal", author_name="C",
                            excerpt="The fog was thick",
                            published_at=datetime.utcnow()))
        db.session.commit()


def test_home_renders_with_seeded_data(client, app):
    _seed_home(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.data.decode()
    assert "celtic-pirate fusion" in body
    assert "Test scuttle" in body
    assert "Raid at Port Royal" in body
    assert "12" in body  # ports_visited
