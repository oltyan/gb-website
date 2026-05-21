from datetime import datetime, timedelta

from flask import Blueprint, render_template

from app.models import Inquiry, Post, TourDate

bp = Blueprint("admin", __name__)


def _require_group(view):
    from functools import wraps

    @wraps(view)
    def wrapper(*args, **kwargs):
        from . import require_admin_group

        return require_admin_group(view)(*args, **kwargs)

    return wrapper


@bp.get("/")
@_require_group
def dashboard():
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    upcoming = (
        TourDate.query.filter(TourDate.status.in_(("confirmed", "tentative")))
        .filter(TourDate.starts_at >= datetime.utcnow() - timedelta(days=1))
        .order_by(TourDate.starts_at)
        .limit(3)
        .all()
    )
    new_inquiries = Inquiry.query.filter_by(status="new").count()
    return render_template(
        "admin/dashboard.html",
        recent_posts=recent_posts,
        upcoming=upcoming,
        new_inquiries=new_inquiries,
    )
