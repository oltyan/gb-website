import os
import pytest

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-do-not-use-in-prod")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OIDC_CLIENT_ID", "test-client")
os.environ.setdefault("OIDC_CLIENT_SECRET", "test-secret")
os.environ.setdefault("OIDC_DISCOVERY_URL", "https://example.test/.well-known/openid-configuration")
os.environ.setdefault("OIDC_GROUP_REQUIRED", "gb-developer")
os.environ.setdefault("CDN_BASE_URL", "https://design-assets.musicalmycology.org/")
os.environ.setdefault("S3_BUCKET", "__PLACEHOLDER__")
os.environ.setdefault("S3_PREFIX", "grogblossoms/")
os.environ.setdefault("CONTACT_EMAIL", "chris@example.test")


@pytest.fixture
def app():
    from app import create_app
    app = create_app(config_name="testing")
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        from app.extensions import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
