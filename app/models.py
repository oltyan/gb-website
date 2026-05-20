"""SQLAlchemy 2.0 typed declarative models."""
from __future__ import annotations

import json
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
