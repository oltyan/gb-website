from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Optional

from app.models import MerchItem

from . import bp
from ._crud import register_crud


class MerchItemForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    image_url = StringField("Image URL (CDN)", validators=[Optional(), URL()])
    price_display = StringField('Price (display, e.g. "$25")', validators=[Optional()])
    external_url = StringField("Buy URL", validators=[DataRequired(), URL()])
    in_stock = BooleanField("In stock", default=True)
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp,
    prefix="merch",
    label="Merch Item",
    model=MerchItem,
    form_cls=MerchItemForm,
    list_cols=[
        ("Name", lambda m: m.name),
        ("Price", lambda m: m.price_display),
        ("Stock", lambda m: "✓" if m.in_stock else "—"),
    ],
    order_by=MerchItem.sort_order,
)
