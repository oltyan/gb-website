import pytest
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
