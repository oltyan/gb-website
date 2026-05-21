from flask import abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

from app.extensions import db
from app.models import Post
from app.services.blocks import BLOCK_TYPES
from . import bp, require_admin_group
from ._crud import register_crud


class PostForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired(), Length(max=255)])
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    author_name = StringField("Author", validators=[DataRequired(), Length(max=255)])
    published_at = DateTimeLocalField("Published at", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    hero_image_url = StringField("Hero image URL", validators=[Optional(), URL()])
    excerpt = TextAreaField("Excerpt", validators=[Optional()])
    body_md = TextAreaField("Legacy markdown (only used if no blocks)", validators=[Optional()])


# Register generic CRUD for list/new/delete; override edit.
register_crud(
    bp, prefix="posts", label="Ship's Log Post",
    model=Post, form_cls=PostForm,
    list_cols=[
        ("Title", lambda p: p.title),
        ("Slug", lambda p: p.slug),
        ("Published", lambda p: p.published_at.strftime("%Y-%m-%d %H:%M") if p.published_at else "draft"),
    ],
    order_by=Post.created_at.desc(),
    exclude=("edit",),
)


# Replace the generic edit endpoint with one that uses the block editor template.
@bp.route("/posts/<int:id>", methods=("GET", "POST"), endpoint="posts_edit")
@require_admin_group
def posts_edit(id: int):
    post = db.session.get(Post, id) or abort(404)
    form = PostForm(obj=post)
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(post)
        db.session.commit()
        flash("Post fields saved.", "success")
        return redirect(url_for("admin.posts_edit", id=id))
    return render_template("admin/posts_edit.html",
                           post=post, form=form, block_types=list(BLOCK_TYPES))
