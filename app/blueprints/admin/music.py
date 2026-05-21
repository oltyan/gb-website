from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL

from app.models import MusicTrack
from . import bp
from ._crud import register_crud


class MusicTrackForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    release_name = StringField("Release", validators=[Optional()])
    audio_url = StringField("Audio URL (CDN)", validators=[Optional(), URL()])
    bandcamp_url = StringField("Bandcamp URL", validators=[Optional(), URL()])
    spotify_url = StringField("Spotify URL", validators=[Optional(), URL()])
    apple_music_url = StringField("Apple Music URL", validators=[Optional(), URL()])
    duration_sec = IntegerField("Duration (sec)", validators=[Optional()])
    cover_url = StringField("Cover image URL", validators=[Optional(), URL()])
    release_date = DateField("Release date", validators=[Optional()])
    lyrics = TextAreaField("Lyrics", validators=[Optional()])
    sort_order = IntegerField("Sort order", default=0)


register_crud(
    bp, prefix="music", label="Music Track",
    model=MusicTrack, form_cls=MusicTrackForm,
    list_cols=[
        ("Title", lambda t: t.title),
        ("Release", lambda t: t.release_name or "—"),
        ("Date", lambda t: t.release_date.isoformat() if t.release_date else "—"),
    ],
    order_by=MusicTrack.sort_order,
)
