from datetime import datetime
from flask import Blueprint, abort, render_template

from app.extensions import db
from app.models import (
    CrewMember, Gallery, MerchItem, MusicTrack, Post, PressAsset,
    Scuttlebutt, SiteSettings, TourDate,
)

bp = Blueprint("public", __name__)


def _live_scuttlebutts():
    return [s for s in Scuttlebutt.query.order_by(Scuttlebutt.sort_order).all() if s.is_visible()]


@bp.get("/")
def home():
    settings = SiteSettings.get_or_create()
    scuttle = _live_scuttlebutts()
    recent = (Post.query
              .filter(Post.published_at.isnot(None))
              .filter(Post.published_at <= datetime.utcnow())
              .order_by(Post.published_at.desc())
              .limit(3).all())
    return render_template("public/home.html",
                           settings=settings, scuttlebutts=scuttle, posts=recent)


@bp.get("/log")
def log_index():
    posts = (Post.query
             .filter(Post.published_at.isnot(None))
             .filter(Post.published_at <= datetime.utcnow())
             .order_by(Post.published_at.desc()).all())
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
    upcoming = (TourDate.query
                .filter(TourDate.status.in_(("confirmed", "tentative")))
                .filter(TourDate.starts_at >= now)
                .order_by(TourDate.starts_at).all())
    past = (TourDate.query
            .filter((TourDate.status == "past") | (TourDate.starts_at < now))
            .order_by(TourDate.starts_at.desc()).all())
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
