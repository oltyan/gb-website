from flask import abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Inquiry
from . import bp, require_admin_group


@bp.get("/inquiries/", endpoint="inquiries_list")
@require_admin_group
def inquiries_list():
    items = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template("admin/inquiries_list.html", items=items)


@bp.get("/inquiries/<int:id>", endpoint="inquiries_detail")
@require_admin_group
def inquiries_detail(id: int):
    inq = db.session.get(Inquiry, id) or abort(404)
    return render_template("admin/inquiries_detail.html", inq=inq)


@bp.post("/inquiries/<int:id>/status", endpoint="inquiries_status")
@require_admin_group
def inquiries_status(id: int):
    inq = db.session.get(Inquiry, id) or abort(404)
    new_status = request.form.get("status")
    if new_status in ("new", "replied", "archived"):
        inq.status = new_status
        db.session.commit()
        flash(f"Marked {new_status}.", "success")
    return redirect(url_for("admin.inquiries_detail", id=id))
