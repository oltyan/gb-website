import re
from datetime import datetime, timedelta

from app.extensions import db
from app.models import SiteSettings, TourDate, User


def _login_as_admin(client, app):
    with app.app_context():
        u = User(oidc_sub="admin-ports", email="a@b", display_name="A")
        u.groups = ["gb-developer"]
        db.session.add(u)
        db.session.commit()
        uid = u.id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True


def _show(name: str, starts_at: datetime, status: str) -> TourDate:
    return TourDate(
        event_name=name, venue="V", city="C", state="CO", starts_at=starts_at, status=status
    )


def _home_ports_counter(client) -> int:
    body = client.get("/").data.decode()
    match = re.search(r">\s*(\d+)\s*</div>\s*<div[^>]*>\s*Ports Visited", body)
    assert match, "Ports Visited counter not found on the home page"
    return int(match.group(1))


def test_ports_visited_counts_past_shows_not_the_settings_number(client, app):
    now = datetime.utcnow()
    with app.app_context():
        SiteSettings.get_or_create().ports_visited = 99  # legacy manual value: ignored
        db.session.add_all(
            [
                _show("Marked past", now - timedelta(days=30), "past"),
                _show("Confirmed but already happened", now - timedelta(days=2), "confirmed"),
                _show("Upcoming", now + timedelta(days=30), "confirmed"),
            ]
        )
        db.session.commit()

    assert _home_ports_counter(client) == 2


def test_ports_visited_is_zero_with_no_shows(client, app):
    assert _home_ports_counter(client) == 0


def test_ports_visited_matches_the_manifest_list(client, app):
    now = datetime.utcnow()
    with app.app_context():
        db.session.add_all(
            [_show(f"Past {i}", now - timedelta(days=10 + i), "past") for i in range(3)]
            + [_show("Upcoming", now + timedelta(days=5), "tentative")]
        )
        db.session.commit()

    manifest = client.get("/manifest").data.decode()
    past_section = manifest.split("Ports Visited", 1)[1]
    assert _home_ports_counter(client) == past_section.count("<li") == 3


def test_admin_settings_no_longer_offers_a_manual_ports_field(client, app):
    _login_as_admin(client, app)
    body = client.get("/admin/settings/").data.decode()
    assert 'name="ports_visited"' not in body
    assert 'name="grog_pints"' in body
