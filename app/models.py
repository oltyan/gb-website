"""SQLAlchemy 2.0 typed declarative models."""

from __future__ import annotations

import json
from datetime import date, datetime

from flask_login import UserMixin
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oidc_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    groups_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def groups(self) -> list[str]:
        try:
            return json.loads(self.groups_json or "[]")
        except json.JSONDecodeError:
            return []

    @groups.setter
    def groups(self, value: list[str]) -> None:
        self.groups_json = json.dumps(value)

    def in_group(self, name: str) -> bool:
        return name in self.groups


class Asset(db.Model):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(1024))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(127), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    caption: Mapped[str | None] = mapped_column(String(512), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    author_name: Mapped[str] = mapped_column(String(255), default="The Crew")
    hero_image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, default="")
    body_md: Mapped[str] = mapped_column(
        Text, default=""
    )  # Phase 3 uses this; Phase 6 migrates to blocks
    blocks: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def is_live(self) -> bool:
        return self.published_at is not None and self.published_at <= datetime.utcnow()


class CrewMember(db.Model):
    __tablename__ = "crew_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))
    portrait_url: Mapped[str] = mapped_column(String(1024), default="")
    quote: Mapped[str] = mapped_column(Text, default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    entry_no: Mapped[str] = mapped_column(String(16), default="")
    tilt: Mapped[str] = mapped_column(String(8), default="left")  # 'left' | 'right'
    accent: Mapped[str] = mapped_column(String(8), default="white")  # 'white' | 'amber' | 'red'
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)


class TourDate(db.Model):
    __tablename__ = "tour_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_name: Mapped[str] = mapped_column(String(255))
    venue: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(8))
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ticket_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), default="confirmed", index=True
    )  # confirmed|tentative|past
    notes: Mapped[str] = mapped_column(Text, default="")


class Gallery(db.Model):
    __tablename__ = "galleries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    cover_image_url: Mapped[str] = mapped_column(String(1024), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[list[GalleryImage]] = relationship(
        back_populates="gallery",
        cascade="all, delete-orphan",
        order_by="GalleryImage.sort_order",
    )


class GalleryImage(db.Model):
    __tablename__ = "gallery_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gallery_id: Mapped[int] = mapped_column(ForeignKey("galleries.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String(1024))
    caption: Mapped[str] = mapped_column(String(512), default="")
    alt_text: Mapped[str] = mapped_column(String(512), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    gallery: Mapped[Gallery] = relationship(back_populates="images")


class MusicTrack(db.Model):
    __tablename__ = "music_tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    release_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bandcamp_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    spotify_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    apple_music_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lyrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class MerchItem(db.Model):
    __tablename__ = "merch_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(1024), default="")
    price_display: Mapped[str] = mapped_column(String(32), default="")
    external_url: Mapped[str] = mapped_column(String(1024), default="")
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class PressAsset(db.Model):
    __tablename__ = "press_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(1024))
    kind: Mapped[str] = mapped_column(String(16), default="other")
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Inquiry(db.Model):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), default="general", index=True)
    from_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Scuttlebutt(db.Model):
    __tablename__ = "scuttlebutts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    link_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    accent: Mapped[str] = mapped_column(String(8), default="amber")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def is_visible(self) -> bool:
        return self.expires_at is None or self.expires_at > datetime.utcnow()


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hero_quote: Mapped[str] = mapped_column(Text, default="")
    hero_image_url: Mapped[str] = mapped_column(String(1024), default="")
    home_background_url: Mapped[str] = mapped_column(String(1024), default="")
    logo_url: Mapped[str] = mapped_column(String(1024), default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    social_links: Mapped[list] = mapped_column(JSON, default=list)
    footer_text: Mapped[str] = mapped_column(
        Text, default="© 2026 THE GROG BLOSSOMS. NO QUARTER GIVEN."
    )
    ports_visited: Mapped[int] = mapped_column(Integer, default=0)
    grog_pints: Mapped[str] = mapped_column(String(32), default="0")

    @classmethod
    def get_or_create(cls) -> SiteSettings:
        instance = db.session.get(cls, 1)
        if instance is None:
            instance = cls(id=1)
            db.session.add(instance)
            db.session.commit()
        return instance
