from app.extensions import db
from app.models import Post, User


def _login_as_admin(client, app):
    with app.app_context():
        u = User(oidc_sub="admin-1", email="a@b", display_name="A")
        u.groups = ["gb-developer"]
        db.session.add(u); db.session.commit()
        uid = u.id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True


def test_post_list_empty(client, app):
    _login_as_admin(client, app)
    response = client.get("/admin/posts/")
    assert response.status_code == 200


def test_post_create(client, app):
    _login_as_admin(client, app)
    response = client.post(
        "/admin/posts/new",
        data={
            "slug": "hello", "title": "Hello World",
            "author_name": "Chris", "excerpt": "first post",
            "body_md": "# Hi", "hero_image_url": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Post.query.filter_by(slug="hello").one() is not None


def test_post_edit(client, app):
    with app.app_context():
        p = Post(slug="x", title="X", author_name="A", excerpt="")
        db.session.add(p); db.session.commit()
        pid = p.id
    _login_as_admin(client, app)
    response = client.post(
        f"/admin/posts/{pid}",
        data={"slug": "x", "title": "Updated",
              "author_name": "A", "excerpt": "", "body_md": "", "hero_image_url": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Post, pid).title == "Updated"


def test_post_delete(client, app):
    with app.app_context():
        p = Post(slug="z", title="Z", author_name="A", excerpt="")
        db.session.add(p); db.session.commit()
        pid = p.id
    _login_as_admin(client, app)
    response = client.post(f"/admin/posts/{pid}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Post, pid) is None


import pytest


@pytest.mark.parametrize("prefix", ["crew", "tour_dates", "music", "merch", "press", "scuttlebutt"])
def test_admin_list_route_renders(client, app, prefix):
    _login_as_admin(client, app)
    response = client.get(f"/admin/{prefix}/")
    assert response.status_code == 200


@pytest.mark.parametrize("prefix", ["crew", "tour_dates", "music", "merch", "press", "scuttlebutt"])
def test_admin_new_route_renders(client, app, prefix):
    _login_as_admin(client, app)
    response = client.get(f"/admin/{prefix}/new")
    assert response.status_code == 200


def test_inquiries_inbox_renders(client, app):
    with app.app_context():
        from app.models import Inquiry
        from app.extensions import db
        i = Inquiry(kind="booking", from_name="A", email="a@b", message="hello")
        db.session.add(i); db.session.commit()
    _login_as_admin(client, app)
    r = client.get("/admin/inquiries/")
    assert r.status_code == 200
    assert b"booking" in r.data or b"BOOKING" in r.data


def test_inquiry_status_update(client, app):
    with app.app_context():
        from app.models import Inquiry
        from app.extensions import db
        i = Inquiry(kind="general", from_name="A", email="a@b", message="x")
        db.session.add(i); db.session.commit()
        iid = i.id
    _login_as_admin(client, app)
    r = client.post(f"/admin/inquiries/{iid}/status",
                    data={"status": "replied"}, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        from app.models import Inquiry
        from app.extensions import db
        assert db.session.get(Inquiry, iid).status == "replied"
