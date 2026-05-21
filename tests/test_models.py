from datetime import datetime, timedelta

from app.extensions import db
from app.models import (
    Asset,
    CrewMember,
    Gallery,
    GalleryImage,
    Inquiry,
    MerchItem,
    MusicTrack,
    Post,
    PressAsset,
    Scuttlebutt,
    SiteSettings,
    TourDate,
)


def test_asset_creates(app):
    with app.app_context():
        a = Asset(
            key="grogblossoms/img/2026/foo.jpg",
            url="https://design-assets.musicalmycology.org/grogblossoms/img/2026/foo.jpg",
            filename="foo.jpg",
            content_type="image/jpeg",
            size_bytes=12345,
        )
        db.session.add(a)
        db.session.commit()
        assert a.id is not None


def test_post_blocks_default_to_empty_list(app):
    with app.app_context():
        p = Post(slug="hello", title="Hello", author_name="Chris", excerpt="")
        db.session.add(p)
        db.session.commit()
        assert p.blocks == []


def test_post_published_predicate(app):
    with app.app_context():
        published = Post(
            slug="a",
            title="A",
            author_name="x",
            excerpt="",
            published_at=datetime.utcnow() - timedelta(days=1),
        )
        draft = Post(slug="b", title="B", author_name="x", excerpt="")
        future = Post(
            slug="c",
            title="C",
            author_name="x",
            excerpt="",
            published_at=datetime.utcnow() + timedelta(days=1),
        )
        for p in (published, draft, future):
            db.session.add(p)
        db.session.commit()
        assert published.is_live() is True
        assert draft.is_live() is False
        assert future.is_live() is False


def test_crew_member_tilt_enum(app):
    with app.app_context():
        c = CrewMember(
            slug="siren",
            name="The Siren",
            role="Fiddle",
            portrait_url="",
            quote="",
            entry_no="002",
            tilt="left",
            accent="white",
            sort_order=0,
        )
        db.session.add(c)
        db.session.commit()
        assert c.tilt == "left"


def test_tour_date_status_filter(app):
    with app.app_context():
        for status in ("confirmed", "tentative", "past"):
            db.session.add(
                TourDate(
                    event_name=f"E-{status}",
                    venue="V",
                    city="C",
                    state="CA",
                    starts_at=datetime.utcnow(),
                    status=status,
                )
            )
        db.session.commit()
        live = TourDate.query.filter(TourDate.status.in_(("confirmed", "tentative"))).all()
        assert len(live) == 2


def test_gallery_with_images(app):
    with app.app_context():
        g = Gallery(
            slug="gigs-2026", title="Gigs 2026", description="", cover_image_url="", sort_order=0
        )
        db.session.add(g)
        db.session.commit()
        for i in range(3):
            db.session.add(
                GalleryImage(
                    gallery_id=g.id,
                    image_url=f"x{i}",
                    caption=f"c{i}",
                    alt_text=f"a{i}",
                    sort_order=i,
                )
            )
        db.session.commit()
        fresh = db.session.get(Gallery, g.id)
        assert len(fresh.images) == 3
        assert [im.sort_order for im in fresh.images] == [0, 1, 2]


def test_music_track_minimal(app):
    with app.app_context():
        t = MusicTrack(title="Heave Ho", sort_order=0)
        db.session.add(t)
        db.session.commit()
        assert t.id is not None


def test_merch_item_in_stock_defaults_true(app):
    with app.app_context():
        m = MerchItem(
            name="Tee",
            description="",
            image_url="",
            price_display="$25",
            external_url="https://x",
            sort_order=0,
        )
        db.session.add(m)
        db.session.commit()
        assert m.in_stock is True


def test_press_asset_kind_enum(app):
    with app.app_context():
        p = PressAsset(title="Bio", file_url="https://x", kind="bio", description="", sort_order=0)
        db.session.add(p)
        db.session.commit()
        assert p.kind == "bio"


def test_inquiry_defaults(app):
    with app.app_context():
        i = Inquiry(kind="booking", from_name="X", email="x@y", message="hello")
        db.session.add(i)
        db.session.commit()
        assert i.status == "new"
        assert i.created_at is not None


def test_scuttlebutt_expiry(app):
    with app.app_context():
        live = Scuttlebutt(text="now", accent="amber", sort_order=0)
        expired = Scuttlebutt(
            text="old", accent="red", sort_order=1, expires_at=datetime.utcnow() - timedelta(days=1)
        )
        future = Scuttlebutt(
            text="future",
            accent="white",
            sort_order=2,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        for s in (live, expired, future):
            db.session.add(s)
        db.session.commit()
        assert live.is_visible() is True
        assert expired.is_visible() is False
        assert future.is_visible() is True


def test_site_settings_singleton_get_or_create(app):
    with app.app_context():
        s = SiteSettings.get_or_create()
        s2 = SiteSettings.get_or_create()
        assert s.id == 1 and s2.id == 1
        assert SiteSettings.query.count() == 1
