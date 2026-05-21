import io
import pytest

from app.services.storage import (
    UploaderNotProvisioned, register_url, upload,
)


def test_upload_raises_when_not_provisioned(app):
    with app.app_context():
        with pytest.raises(UploaderNotProvisioned):
            upload(io.BytesIO(b"x"), "x.jpg", "image/jpeg")


def test_register_url_creates_asset(app):
    with app.app_context():
        a = register_url(
            "https://design-assets.musicalmycology.org/grogblossoms/img/foo.jpg",
            caption="Foo",
        )
        assert a.id is not None
        assert a.key == "grogblossoms/img/foo.jpg"
        assert a.caption == "Foo"


def test_register_url_rejects_wrong_prefix(app):
    with app.app_context():
        with pytest.raises(ValueError):
            register_url("https://evil.test/grogblossoms/x.jpg")
