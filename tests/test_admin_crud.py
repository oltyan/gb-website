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
