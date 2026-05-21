from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Optional

from app.models import Scuttlebutt

from . import bp
from ._crud import register_crud


class ScuttlebuttForm(FlaskForm):
    text = TextAreaField("Text", validators=[DataRequired()])
    link_url = StringField("Link URL", validators=[Optional(), URL()])
    accent = SelectField(
        "Accent (mark)",
        choices=[
            ("amber", "Amber"),
            ("red", "Red"),
            ("white", "White"),
        ],
    )
    sort_order = IntegerField("Sort order", default=0)
    expires_at = DateTimeLocalField("Expires at", validators=[Optional()], format="%Y-%m-%dT%H:%M")


register_crud(
    bp,
    prefix="scuttlebutt",
    label="Scuttlebutt",
    model=Scuttlebutt,
    form_cls=ScuttlebuttForm,
    list_cols=[
        ("Text", lambda s: (s.text[:60] + "…") if len(s.text) > 60 else s.text),
        ("Accent", lambda s: s.accent),
        ("Expires", lambda s: s.expires_at.strftime("%Y-%m-%d") if s.expires_at else "—"),
    ],
    order_by=Scuttlebutt.sort_order,
)
