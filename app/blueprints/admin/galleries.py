from flask import abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Optional

from app.extensions import db
from app.models import Gallery, GalleryImage

from . import bp, require_admin_group


class GalleryForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    cover_image_url = StringField("Cover image URL (CDN)", validators=[Optional(), URL()])
    sort_order = IntegerField("Sort order", default=0)


class GalleryImageForm(FlaskForm):
    image_url = StringField("Image URL (CDN)", validators=[DataRequired(), URL()])
    caption = StringField("Caption", validators=[Optional()])
    alt_text = StringField("Alt text", validators=[Optional()])


@bp.get("/galleries/", endpoint="galleries_list")
@require_admin_group
def galleries_list():
    items = Gallery.query.order_by(Gallery.sort_order).all()
    return render_template(
        "admin/_list.html",
        label="Gallery",
        prefix="galleries",
        items=items,
        cols=[
            ("Title", lambda g: g.title),
            ("Slug", lambda g: g.slug),
            ("Images", lambda g: len(g.images)),
        ],
    )


@bp.route("/galleries/new", methods=("GET", "POST"), endpoint="galleries_new")
@require_admin_group
def galleries_new():
    form = GalleryForm()
    if form.validate_on_submit():
        g = Gallery()
        form.populate_obj(g)
        db.session.add(g)
        db.session.commit()
        flash("Gallery created.", "success")
        return redirect(url_for("admin.galleries_edit", id=g.id))
    return render_template(
        "admin/_form.html", label="Gallery", prefix="galleries", form=form, mode="new"
    )


@bp.route("/galleries/<int:id>", methods=("GET", "POST"), endpoint="galleries_edit")
@require_admin_group
def galleries_edit(id: int):
    g = db.session.get(Gallery, id) or abort(404)
    form = GalleryForm(obj=g)
    image_form = GalleryImageForm()
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(g)
        db.session.commit()
        flash("Gallery saved.", "success")
        return redirect(url_for("admin.galleries_edit", id=id))
    return render_template("admin/galleries_edit.html", gallery=g, form=form, image_form=image_form)


@bp.post("/galleries/<int:id>/delete", endpoint="galleries_delete")
@require_admin_group
def galleries_delete(id: int):
    g = db.session.get(Gallery, id) or abort(404)
    db.session.delete(g)
    db.session.commit()
    flash("Gallery deleted.", "success")
    return redirect(url_for("admin.galleries_list"))


@bp.post("/galleries/<int:id>/images/add", endpoint="galleries_add_image")
@require_admin_group
def galleries_add_image(id: int):
    g = db.session.get(Gallery, id) or abort(404)
    form = GalleryImageForm()
    if form.validate_on_submit():
        next_order = max((im.sort_order for im in g.images), default=-1) + 1
        img = GalleryImage(
            gallery_id=g.id,
            image_url=form.image_url.data,
            caption=form.caption.data or "",
            alt_text=form.alt_text.data or "",
            sort_order=next_order,
        )
        db.session.add(img)
        db.session.commit()
        flash("Image added.", "success")
    else:
        flash(
            "Image add failed: "
            + "; ".join(f"{f}: {','.join(errs)}" for f, errs in form.errors.items()),
            "error",
        )
    return redirect(url_for("admin.galleries_edit", id=id))


@bp.post("/galleries/<int:gid>/images/<int:iid>/delete", endpoint="galleries_delete_image")
@require_admin_group
def galleries_delete_image(gid: int, iid: int):
    img = db.session.get(GalleryImage, iid) or abort(404)
    if img.gallery_id != gid:
        abort(404)
    db.session.delete(img)
    db.session.commit()
    flash("Image removed.", "success")
    return redirect(url_for("admin.galleries_edit", id=gid))


@bp.post("/galleries/<int:gid>/images/<int:iid>/move", endpoint="galleries_move_image")
@require_admin_group
def galleries_move_image(gid: int, iid: int):
    direction = request.form.get("direction", "up")
    img = db.session.get(GalleryImage, iid) or abort(404)
    if img.gallery_id != gid:
        abort(404)
    siblings = sorted(img.gallery.images, key=lambda i: i.sort_order)
    idx = next(i for i, x in enumerate(siblings) if x.id == iid)
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap_idx < len(siblings):
        img.sort_order, siblings[swap_idx].sort_order = (
            siblings[swap_idx].sort_order,
            img.sort_order,
        )
        db.session.commit()
    return redirect(url_for("admin.galleries_edit", id=gid))
