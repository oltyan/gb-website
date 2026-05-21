from flask import flash, redirect, render_template, request, url_for

from app.models import Asset
from app.services.storage import register_url
from . import bp, require_admin_group


@bp.get("/assets/", endpoint="assets_list")
@require_admin_group
def assets_list():
    items = Asset.query.order_by(Asset.uploaded_at.desc()).all()
    return render_template("admin/assets_list.html", items=items)


@bp.post("/assets/register", endpoint="assets_register")
@require_admin_group
def assets_register():
    url = (request.form.get("url") or "").strip()
    caption = (request.form.get("caption") or "").strip()
    try:
        register_url(url, caption=caption)
        flash("Asset registered.", "success")
    except ValueError as exc:
        flash(f"Rejected: {exc}", "error")
    return redirect(url_for("admin.assets_list"))
