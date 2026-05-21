from datetime import date, datetime

from flask import Blueprint, abort, render_template, request

from app.extensions import db
from app.models import (
    CrewMember,
    Gallery,
    Inquiry,
    MerchItem,
    MusicTrack,
    Post,
    PressAsset,
    Scuttlebutt,
    SiteSettings,
    TourDate,
)
from app.services.email import send_inquiry_notification

bp = Blueprint("public", __name__)


def _live_scuttlebutts():
    return [s for s in Scuttlebutt.query.order_by(Scuttlebutt.sort_order).all() if s.is_visible()]


@bp.get("/")
def home():
    settings = SiteSettings.get_or_create()
    scuttle = _live_scuttlebutts()
    recent = (
        Post.query.filter(Post.published_at.isnot(None))
        .filter(Post.published_at <= datetime.utcnow())
        .order_by(Post.published_at.desc())
        .limit(3)
        .all()
    )
    return render_template(
        "public/home.html", settings=settings, scuttlebutts=scuttle, posts=recent
    )


@bp.get("/log")
def log_index():
    posts = (
        Post.query.filter(Post.published_at.isnot(None))
        .filter(Post.published_at <= datetime.utcnow())
        .order_by(Post.published_at.desc())
        .all()
    )
    return render_template("public/log_index.html", posts=posts)


@bp.get("/log/<slug>")
def log_detail(slug: str):
    post = Post.query.filter_by(slug=slug).one_or_none()
    if post is None or not post.is_live():
        abort(404)
    return render_template("public/log_detail.html", post=post)


@bp.get("/manifest")
def manifest():
    now = datetime.utcnow()
    upcoming = (
        TourDate.query.filter(TourDate.status.in_(("confirmed", "tentative")))
        .filter(TourDate.starts_at >= now)
        .order_by(TourDate.starts_at)
        .all()
    )
    past = (
        TourDate.query.filter((TourDate.status == "past") | (TourDate.starts_at < now))
        .order_by(TourDate.starts_at.desc())
        .all()
    )
    return render_template("public/manifest.html", upcoming=upcoming, past=past)


@bp.get("/crew")
def crew():
    members = CrewMember.query.order_by(CrewMember.sort_order).all()
    return render_template("public/crew.html", members=members)


@bp.get("/booty")
def booty():
    tracks = MusicTrack.query.order_by(MusicTrack.sort_order).all()
    merch = MerchItem.query.order_by(MerchItem.sort_order).all()
    return render_template("public/booty.html", tracks=tracks, merch=merch)


@bp.get("/gallery")
def gallery_index():
    galleries = Gallery.query.order_by(Gallery.sort_order).all()
    return render_template("public/gallery_index.html", galleries=galleries)


@bp.get("/gallery/<slug>")
def gallery_detail(slug: str):
    g = Gallery.query.filter_by(slug=slug).one_or_none()
    if g is None:
        abort(404)
    return render_template("public/gallery_detail.html", gallery=g)


@bp.get("/crows-nest")
def crows_nest():
    press = PressAsset.query.order_by(PressAsset.sort_order).all()
    return render_template("public/crows_nest.html", press=press)


@bp.post("/crows-nest/submit")
def crows_nest_submit():
    kind = (request.form.get("kind") or "general").strip()
    if kind not in ("booking", "press", "general"):
        kind = "general"
    from_name = (request.form.get("from_name") or "").strip()
    email = (request.form.get("email") or "").strip()
    message = (request.form.get("message") or "").strip()
    if not from_name or not email or not message:
        return render_template(
            "public/crows_nest.html",
            press=PressAsset.query.order_by(PressAsset.sort_order).all(),
            error="Name, email, and message are required.",
        ), 400

    event_date_raw = (request.form.get("event_date") or "").strip()
    event_date_val: date | None = None
    if event_date_raw:
        try:
            event_date_val = date.fromisoformat(event_date_raw)
        except ValueError:
            event_date_val = None

    inq = Inquiry(
        kind=kind,
        from_name=from_name,
        email=email,
        phone=(request.form.get("phone") or "").strip() or None,
        event_date=event_date_val,
        venue=(request.form.get("venue") or "").strip() or None,
        city=(request.form.get("city") or "").strip() or None,
        message=message,
    )
    db.session.add(inq)
    db.session.commit()
    send_inquiry_notification(inq)
    return render_template("public/crows_nest_thanks.html", inq=inq)
