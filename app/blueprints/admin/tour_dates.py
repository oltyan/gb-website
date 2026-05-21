from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional

from app.models import TourDate

from . import bp
from ._crud import register_crud


class TourDateForm(FlaskForm):
    event_name = StringField("Event", validators=[DataRequired()])
    venue = StringField("Venue", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    state = StringField("State", validators=[DataRequired(), Length(max=8)])
    starts_at = DateTimeLocalField(
        "Starts at", validators=[DataRequired()], format="%Y-%m-%dT%H:%M"
    )
    ends_at = DateTimeLocalField("Ends at", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    ticket_url = StringField("Ticket URL", validators=[Optional(), URL()])
    status = SelectField(
        "Status", choices=[("confirmed", "Confirmed"), ("tentative", "Tentative"), ("past", "Past")]
    )
    notes = TextAreaField("Notes", validators=[Optional()])


register_crud(
    bp,
    prefix="tour_dates",
    label="Tour Date",
    model=TourDate,
    form_cls=TourDateForm,
    list_cols=[
        ("Event", lambda t: t.event_name),
        ("Where", lambda t: f"{t.venue}, {t.city} {t.state}"),
        ("Starts", lambda t: t.starts_at.strftime("%Y-%m-%d %H:%M")),
        ("Status", lambda t: t.status),
    ],
    order_by=TourDate.starts_at.desc(),
)
