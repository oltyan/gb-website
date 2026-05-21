import logging

from flask import flash, redirect, render_template, request, url_for

from app.models import Asset
from app.services.storage import SporeklesError, get_client

from . import bp, require_admin_group

log = logging.getLogger(__name__)


@bp.get("/assets/", endpoint="assets_list")
@require_admin_group
def assets_list():
    items = Asset.query.order_by(Asset.uploaded_at.desc()).all()
    return render_template("admin/assets_list.html", items=items)


@bp.post("/assets/upload", endpoint="assets_upload")
@require_admin_group
def assets_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a file to upload.", "error")
        return redirect(url_for("admin.assets_list"))

    caption = (request.form.get("caption") or "").strip() or None

    try:
        client = get_client()
        asset = client.upload_asset(
            file.stream,
            filename=file.filename,
            content_type=file.mimetype or "application/octet-stream",
            caption=caption,
        )
    except SporeklesError as exc:
        if exc.status_code and exc.status_code < 500:
            flash(f"Upload rejected: {exc}", "error")
        else:
            log.exception("sporekles upload failed: %s", exc)
            flash("Upload failed — see logs.", "error")
        return redirect(url_for("admin.assets_list"))

    flash(f"Uploaded {asset.filename}.", "success")
    return redirect(url_for("admin.assets_list"))
