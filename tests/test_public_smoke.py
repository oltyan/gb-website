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


def test_log_index_and_detail(client, app):
    with app.app_context():
        db.session.add(Post(slug="entry", title="Entry", author_name="C",
                            excerpt="ex", body_md="# Hi\n\npara",
                            published_at=datetime.utcnow()))
        db.session.commit()
    r1 = client.get("/log")
    assert r1.status_code == 200 and b"Entry" in r1.data
    r2 = client.get("/log/entry")
    assert r2.status_code == 200 and b"Hi" in r2.data


def test_log_detail_404s_for_draft(client, app):
    with app.app_context():
        db.session.add(Post(slug="draft", title="X", author_name="C", excerpt="", body_md=""))
        db.session.commit()
    r = client.get("/log/draft")
    assert r.status_code == 404


def test_manifest_lists_upcoming(client, app):
    from app.models import TourDate
    with app.app_context():
        db.session.add(TourDate(event_name="Renfest", venue="V", city="C", state="CA",
                                starts_at=datetime.utcnow().replace(year=2099), status="confirmed"))
        db.session.commit()
    r = client.get("/manifest")
    assert r.status_code == 200 and b"Renfest" in r.data
