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


def test_login_callback_url_is_https_behind_tls_terminating_proxy(client):
    # In production cloudflared terminates TLS and forwards plain HTTP with
    # X-Forwarded-Proto: https. The OIDC provider only authorises the https
    # callback, so the redirect_uri we hand it must honour that header.
    from flask import redirect as _redirect

    with patch("app.blueprints.auth.views.oauth.fa") as mock_fa:
        mock_fa.authorize_redirect.side_effect = lambda uri: _redirect("https://idp.test/?u=" + uri)
        client.get(
            "/auth/login",
            headers={"Host": "www.grogblossoms.com", "X-Forwarded-Proto": "https"},
        )
        (redirect_uri,), _ = mock_fa.authorize_redirect.call_args
    assert redirect_uri == "https://www.grogblossoms.com/auth/oidc/callback"


def test_oidc_client_uses_pkce(app):
    # The identity provider rejects authorization requests without a PKCE
    # code_challenge (error=invalid_request, missing_code_challenge).
    from app.extensions import oauth

    assert oauth.fa.client_kwargs.get("code_challenge_method") == "S256"


def test_oidc_client_does_not_request_unregistered_groups_scope(app):
    # The provider has no `groups` scope and rejects the whole request with
    # invalid_scope / unknown_scope. Group names arrive as a token claim.
    from app.extensions import oauth

    assert "groups" not in oauth.fa.client_kwargs["scope"].split()


def test_oidc_callback_reports_provider_error_instead_of_500(client):
    with patch("app.blueprints.auth.views._fetch_token") as fetch:
        response = client.get(
            "/auth/oidc/callback?error=invalid_scope"
            "&error_description=Invalid+scope.&state=fake"
        )
    assert response.status_code == 400
    assert b"invalid_scope" in response.data
    fetch.assert_not_called()


def test_oidc_callback_accepts_required_group_from_roles_claim(client, app):
    # FusionAuth emits a user's roles on this application as `roles`; a
    # `groups` claim only exists when a populate lambda is bound to the app.
    fake_token = {
        "userinfo": {"sub": "fa-user-003", "email": "r@example.test", "roles": ["gb-developer"]}
    }
    with patch("app.blueprints.auth.views._fetch_token", return_value=fake_token):
        response = client.get("/auth/oidc/callback?code=fake&state=fake")
    assert response.status_code in (302, 303)


def test_oidc_callback_rejects_roles_claim_without_required_group(client, app):
    fake_token = {"userinfo": {"sub": "fa-user-004", "email": "n@example.test", "roles": ["user"]}}
    with patch("app.blueprints.auth.views._fetch_token", return_value=fake_token):
        response = client.get("/auth/oidc/callback?code=fake&state=fake")
    assert response.status_code == 403
