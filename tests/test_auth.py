from unittest.mock import patch

from app.extensions import db
from app.models import User


def test_user_creation_persists(app):
    with app.app_context():
        user = User(
            oidc_sub="abc-123",
            email="chris@example.test",
            display_name="Chris",
            groups_json='["gb-developer"]',
        )
        db.session.add(user)
        db.session.commit()
        fetched = db.session.get(User, user.id)
        assert fetched is not None
        assert fetched.email == "chris@example.test"
        assert "gb-developer" in fetched.groups


def test_user_groups_property_parses_json(app):
    with app.app_context():
        user = User(oidc_sub="x", email="x@y", display_name="x", groups_json='["a","b"]')
        assert user.groups == ["a", "b"]


def test_user_in_group(app):
    with app.app_context():
        user = User(oidc_sub="x", email="x@y", display_name="x", groups_json='["gb-developer"]')
        assert user.in_group("gb-developer") is True
        assert user.in_group("admin") is False


def test_login_redirects_to_oidc_provider(client):
    # Authlib would normally fetch the OIDC discovery doc; in tests the
    # configured URL is unreachable, so we mock the single redirect seam.
    from flask import redirect as _redirect

    fake_authorize_url = (
        "https://oidc-provider.test/authorize"
        "?response_type=code&client_id=test-client"
        "&redirect_uri=http://localhost/auth/oidc/callback&scope=openid+email+profile+groups"
    )
    with patch(
        "app.blueprints.auth.views.oauth.fa.authorize_redirect",
        return_value=_redirect(fake_authorize_url),
    ):
        response = client.get("/auth/login")
    assert response.status_code == 302
    # Authlib redirects to the discovery-derived authorize endpoint
    assert "redirect_uri" in response.location or response.location.startswith("http")


def test_logout_clears_session(client, app):
    with client.session_transaction() as sess:
        sess["_user_id"] = "1"
    response = client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "_user_id" not in sess


def test_oidc_callback_creates_user_and_logs_in(client, app):
    fake_userinfo = {
        "sub": "fa-user-001",
        "email": "chris@example.test",
        "name": "Chris O.",
        "groups": ["gb-developer", "other"],
    }
    fake_token = {"userinfo": fake_userinfo}

    with patch("app.blueprints.auth.views._fetch_token", return_value=fake_token):
        response = client.get("/auth/oidc/callback?code=fake&state=fake")
        assert response.status_code in (302, 303)

    from app.models import User

    with app.app_context():
        user = User.query.filter_by(oidc_sub="fa-user-001").one_or_none()
        assert user is not None
        assert user.email == "chris@example.test"
        assert "gb-developer" in user.groups


def test_oidc_callback_rejects_user_without_required_group(client, app):
    fake_userinfo = {
        "sub": "fa-user-002",
        "email": "norights@example.test",
        "name": "No Rights",
        "groups": ["other"],
    }
    fake_token = {"userinfo": fake_userinfo}

    with patch("app.blueprints.auth.views._fetch_token", return_value=fake_token):
        response = client.get("/auth/oidc/callback?code=fake&state=fake")
        assert response.status_code == 403
