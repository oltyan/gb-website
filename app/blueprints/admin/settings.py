from flask import flash, redirect, render_template, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import URL, Optional

from app.extensions import db
from app.models import SiteSettings

from . import bp, require_admin_group


class SiteSettingsForm(FlaskForm):
    hero_quote = TextAreaField("Hero quote", validators=[Optional()])
    hero_image_url = StringField("Hero image URL", validators=[Optional(), URL()])
    logo_url = StringField("Logo URL", validators=[Optional(), URL()])
    contact_email = StringField("Contact email", validators=[Optional()])
    footer_text = StringField("Footer text", validators=[Optional()])
    ports_visited = IntegerField("Ports visited (stat)", default=0)
    grog_pints = StringField("Grog pints (stat, e.g. '100+')", validators=[Optional()])


@bp.route("/settings/", methods=("GET", "POST"), endpoint="settings")
@require_admin_group
def settings():
    s = SiteSettings.get_or_create()
    form = SiteSettingsForm(obj=s)
    if form.validate_on_submit():
        form.populate_obj(s)
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", form=form)
