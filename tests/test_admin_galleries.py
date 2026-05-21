from app.extensions import db
from app.models import Gallery, GalleryImage, User


def _login(client, app):
    with app.app_context():
        u = User(oidc_sub="g-admin", email="a@b", display_name="A")
        u.groups = ["gb-developer"]
        db.session.add(u)
        db.session.commit()
        uid = u.id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True


def test_gallery_create(client, app):
    _login(client, app)
    response = client.post(
        "/admin/galleries/new",
        data={
            "slug": "g1",
            "title": "Gigs",
            "description": "",
            "cover_image_url": "",
            "sort_order": 0,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Gallery.query.filter_by(slug="g1").one() is not None


def test_gallery_add_image(client, app):
    with app.app_context():
        g = Gallery(slug="g2", title="t", description="", cover_image_url="", sort_order=0)
        db.session.add(g)
        db.session.commit()
        gid = g.id
    _login(client, app)
    response = client.post(
        f"/admin/galleries/{gid}/images/add",
        data={
            "image_url": "https://cdn.example/x.jpg",
            "caption": "Pier",
            "alt_text": "Pier at dusk",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        g2 = db.session.get(Gallery, gid)
        assert len(g2.images) == 1
        assert g2.images[0].caption == "Pier"


def test_gallery_remove_image(client, app):
    with app.app_context():
        g = Gallery(slug="g3", title="t", description="", cover_image_url="", sort_order=0)
        db.session.add(g)
        db.session.commit()
        img = GalleryImage(gallery_id=g.id, image_url="x", caption="", alt_text="", sort_order=0)
        db.session.add(img)
        db.session.commit()
        gid, iid = g.id, img.id
    _login(client, app)
    response = client.post(f"/admin/galleries/{gid}/images/{iid}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(GalleryImage, iid) is None
