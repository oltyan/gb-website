from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL

from app.models import PressAsset
from . import bp
from ._crud import register_crud


class PressAssetForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    file_url = StringField("File URL (CDN)", validators=[DataRequired(), URL()])
    kind = SelectField("Kind", choices=[
        ("bio", "Bio"), ("logo", "Logo"), ("photo", "Photo"),
        ("rider", "Rider"), ("stage_plot", "Stage plot"),
        ("epk", "EPK"), ("other", "Other"),
    ])
    description = TextAreaField("Description", validators=[Optional()])
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp, prefix="press", label="Press Asset",
    model=PressAsset, form_cls=PressAssetForm,
    list_cols=[
        ("Title", lambda p: p.title),
        ("Kind", lambda p: p.kind),
    ],
    order_by=PressAsset.sort_order,
)
