from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

from app.models import Post
from . import bp
from ._crud import register_crud


class PostForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired(), Length(max=255)])
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    author_name = StringField("Author", validators=[DataRequired(), Length(max=255)])
    published_at = DateTimeLocalField("Published at", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    hero_image_url = StringField("Hero image URL", validators=[Optional(), URL()])
    excerpt = TextAreaField("Excerpt", validators=[Optional()])
    body_md = TextAreaField("Body (Markdown — block editor coming in Phase 6)", validators=[Optional()])


register_crud(
    bp,
    prefix="posts",
    label="Ship's Log Post",
    model=Post,
    form_cls=PostForm,
    list_cols=[
        ("Title", lambda p: p.title),
        ("Slug", lambda p: p.slug),
        ("Published", lambda p: p.published_at.strftime("%Y-%m-%d %H:%M") if p.published_at else "draft"),
    ],
    order_by=Post.created_at.desc(),
)
