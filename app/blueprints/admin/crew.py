from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models import CrewMember

from . import bp
from ._crud import register_crud


class CrewMemberForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired(), Length(max=255)])
    name = StringField("Name", validators=[DataRequired()])
    role = StringField("Role", validators=[DataRequired()])
    portrait_url = StringField("Portrait URL", validators=[Optional()])
    quote = TextAreaField("Quote", validators=[Optional()])
    bio = TextAreaField("Bio", validators=[Optional()])
    entry_no = StringField("Entry #", validators=[Optional()])
    tilt = SelectField("Tilt", choices=[("left", "Left (-1°)"), ("right", "Right (+1°)")])
    accent = SelectField("Accent", choices=[("white", "White"), ("amber", "Amber"), ("red", "Red")])
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp,
    prefix="crew",
    label="Crew Member",
    model=CrewMember,
    form_cls=CrewMemberForm,
    list_cols=[
        ("Name", lambda c: c.name),
        ("Role", lambda c: c.role),
        ("Entry #", lambda c: c.entry_no),
    ],
    order_by=CrewMember.sort_order,
)
