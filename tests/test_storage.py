import io

import pytest
import responses

from app.models import Asset
from app.services.storage import (
    AuthContext,
    SporeklesClient,
    SporeklesError,
)


def _auth():
    return AuthContext(email="admin@example.test", user="admin",
                       groups=["gb-developer"])


def _client():
    return SporeklesClient(
        api_base="http://sporekles.test",
        tenant="gb",
        get_auth=_auth,
    )


@responses.activate
def test_upload_asset_persists_row_from_entry(app):
    responses.post(
        "http://sporekles.test/gb/assets",
        json={
            "ok": True,
            "entry": {
                "slug": "logo",
                "filename": "logo.png",
                "category": "asset",
                "contentType": "image/png",
                "bytes": 1234,
                "url": "https://design-assets.grogblossoms.com/assets/logo.png",
            },
            "invalidationId": "I1",
        },
        status=200,
    )

    with app.app_context():
        asset = _client().upload_asset(
            io.BytesIO(b"\x89PNG..."),
            filename="logo.png",
            content_type="image/png",
            caption="Mark of the Crew",
        )
        assert asset.id is not None
        assert asset.key == "assets/logo.png"
        assert asset.url == "https://design-assets.grogblossoms.com/assets/logo.png"
        assert asset.content_type == "image/png"
        assert asset.size_bytes == 1234
        assert asset.caption == "Mark of the Crew"
        assert Asset.query.count() == 1


@responses.activate
def test_upload_asset_forwards_auth_headers(app):
    captured = {}

    def _capture(req):
        captured["email"] = req.headers.get("X-Auth-Request-Email")
        captured["user"] = req.headers.get("X-Auth-Request-User")
        captured["groups"] = req.headers.get("X-Auth-Request-Groups")
        captured["content_type"] = req.headers.get("Content-Type", "")
        return (
            200,
            {},
            '{"ok":true,"entry":{"slug":"x","filename":"x.png","category":"asset","contentType":"image/png","bytes":1,"url":"https://design-assets.grogblossoms.com/assets/x.png"}}',
        )

    responses.add_callback(
        responses.POST,
        "http://sporekles.test/gb/assets",
        callback=_capture,
    )

    with app.app_context():
        _client().upload_asset(io.BytesIO(b"x"), "x.png", "image/png")

    assert captured["email"] == "admin@example.test"
    assert captured["user"] == "admin"
    assert captured["groups"] == "gb-developer"
    assert captured["content_type"].startswith("multipart/form-data")


@responses.activate
def test_upload_asset_raises_on_4xx_with_error_body(app):
    responses.post(
        "http://sporekles.test/gb/assets",
        json={"ok": False, "error": "filename contains invalid characters"},
        status=400,
    )

    with app.app_context():
        with pytest.raises(SporeklesError) as exc_info:
            _client().upload_asset(io.BytesIO(b"x"), "../bad.png", "image/png")
        assert exc_info.value.status_code == 400
        assert "invalid characters" in str(exc_info.value)
        assert Asset.query.count() == 0


@responses.activate
def test_upload_asset_raises_on_unreachable(app):
    # No responses registered -> connection error
    with app.app_context():
        with pytest.raises(SporeklesError) as exc_info:
            _client().upload_asset(io.BytesIO(b"x"), "x.png", "image/png")
        assert "unreachable" in str(exc_info.value)
