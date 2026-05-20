from flask_login import login_user
from app.models import User
from app.extensions import db


def _make_user(app, groups: list[str]) -> int:
    with app.app_context():
        user = User(oidc_sub=f"sub-{groups}", email="x@y", display_name="X")
        user.groups = groups
        db.session.add(user)
        db.session.commit()
        return user.id


def test_admin_redirects_anonymous_to_login(client):
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_admin_denies_user_without_required_group(client, app):
    uid = _make_user(app, ["other"])
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True
    response = client.get("/admin/")
    assert response.status_code == 403


def test_admin_allows_user_with_required_group(client, app):
    uid = _make_user(app, ["gb-developer"])
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True
    response = client.get("/admin/")
    assert response.status_code == 200
