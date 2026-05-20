from functools import wraps

from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint("admin", __name__)


# Note: require_admin_group is imported in __init__.py to avoid circular import;
# decorator is applied per-view to make intent explicit. The lazy import inside
# the wrapper breaks the cycle at runtime: views.py loads first (so bp exists),
# __init__.py then defines require_admin_group, and by the time any request hits
# this view, the symbol is resolvable.
def _require_group(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        from . import require_admin_group
        return require_admin_group(view)(*args, **kwargs)
    return wrapper


@bp.get("/")
@_require_group
def dashboard():
    return render_template("admin/dashboard.html")
