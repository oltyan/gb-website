import json

from app.extensions import db
from app.models import Post, User


def _login(client, app):
    with app.app_context():
        u = User(oidc_sub="b-admin", email="a@b", display_name="A")
        u.groups = ["gb-developer"]
        db.session.add(u)
        db.session.commit()
        uid = u.id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True


def test_blocks_save_persists(client, app):
    with app.app_context():
        p = Post(slug="bp", title="T", author_name="C", excerpt="")
        db.session.add(p)
        db.session.commit()
        pid = p.id
    _login(client, app)
    payload = [
        {"type": "paragraph", "data": {"markdown": "hi"}},
        {"type": "heading", "data": {"level": 2, "text": "X"}},
    ]
    r = client.post(f"/admin/posts/{pid}/blocks/save", data={"blocks": json.dumps(payload)})
    assert r.status_code in (200, 302)
    with app.app_context():
        fresh = db.session.get(Post, pid)
        assert len(fresh.blocks) == 2
        assert fresh.blocks[0]["type"] == "paragraph"


def test_blocks_add_endpoint_returns_partial(client, app):
    _login(client, app)
    r = client.get("/admin/blocks/new/paragraph")
    assert r.status_code == 200
    assert b"markdown" in r.data.lower() or b"paragraph" in r.data.lower()
