from functools import wraps
from flask import abort, current_app, render_template
from flask_login import current_user

from .views import bp


def require_admin_group(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        required = current_app.config.get("OIDC_GROUP_REQUIRED", "gb-developer")
        if not current_user.is_authenticated:
            from flask import redirect, request, url_for
            return redirect(url_for("auth.login", next=request.path))
        if not current_user.in_group(required):
            return render_template("auth/forbidden.html", required=required), 403
        return view(*args, **kwargs)
    return wrapper


# Apply decorator at blueprint level via before_request hook:
@bp.before_request
def _gate():
    # Defer to the per-view login_required + custom check for clarity.
    pass


__all__ = ["bp", "require_admin_group"]

from . import posts, crew, tour_dates, galleries, music, merch, press, inquiries, scuttlebutt, assets, settings as _settings  # noqa: E402,F401
