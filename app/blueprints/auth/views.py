from datetime import datetime
from urllib.parse import urlparse

from flask import (
    Blueprint, abort, current_app, redirect, render_template, request,
    session, url_for,
)
from flask_login import login_required, login_user, logout_user

from app.extensions import db, oauth
from app.models import User

bp = Blueprint("auth", __name__)


@bp.get("/login")
def login():
    redirect_uri = url_for("auth.oidc_callback", _external=True)
    next_url = request.args.get("next")
    if next_url and _is_safe_next(next_url):
        session["post_login_next"] = next_url
    return oauth.fa.authorize_redirect(redirect_uri)


@bp.get("/oidc/callback")
def oidc_callback():
    token = _fetch_token()
    userinfo = token.get("userinfo") or oauth.fa.userinfo(token=token)
    required_group = current_app.config.get("OIDC_GROUP_REQUIRED", "gb-developer")
    groups = userinfo.get("groups") or []

    if required_group not in groups:
        return render_template("auth/forbidden.html", required=required_group), 403

    sub = userinfo["sub"]
    user = User.query.filter_by(oidc_sub=sub).one_or_none()
    if user is None:
        user = User(oidc_sub=sub, email=userinfo.get("email", ""),
                    display_name=userinfo.get("name", userinfo.get("email", "")))
        db.session.add(user)
    user.email = userinfo.get("email", user.email)
    user.display_name = userinfo.get("name", user.display_name)
    user.groups = list(groups)
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    login_user(user)
    next_url = session.pop("post_login_next", None) or url_for("admin.dashboard")
    return redirect(next_url)


@bp.get("/logout")
def logout():
    logout_user()
    session.pop("_user_id", None)
    return redirect(url_for("public.home"))


def _fetch_token():
    """Wrapped so tests can monkeypatch this single seam."""
    return oauth.fa.authorize_access_token()


def _is_safe_next(target: str) -> bool:
    parsed = urlparse(target)
    return not parsed.netloc and parsed.path.startswith("/")
