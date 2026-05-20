import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    SECRET_KEY: str
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool
    OIDC_CLIENT_ID: str
    OIDC_CLIENT_SECRET: str
    OIDC_DISCOVERY_URL: str
    OIDC_GROUP_REQUIRED: str
    CDN_BASE_URL: str
    S3_BUCKET: str
    S3_PREFIX: str
    S3_REGION: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    CONTACT_EMAIL: str
    SESSION_COOKIE_SECURE: bool
    TESTING: bool
    DEBUG: bool


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def load_config(name: str = "production") -> Config:
    return Config(
        SECRET_KEY=_env("SECRET_KEY") or ("dev" if name != "production" else _require("SECRET_KEY")),
        SQLALCHEMY_DATABASE_URI=_env("DATABASE_URL", "sqlite:///grogblossoms.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        OIDC_CLIENT_ID=_env("OIDC_CLIENT_ID"),
        OIDC_CLIENT_SECRET=_env("OIDC_CLIENT_SECRET"),
        OIDC_DISCOVERY_URL=_env("OIDC_DISCOVERY_URL"),
        OIDC_GROUP_REQUIRED=_env("OIDC_GROUP_REQUIRED", "gb-developer"),
        CDN_BASE_URL=_env("CDN_BASE_URL", "https://design-assets.musicalmycology.org/"),
        S3_BUCKET=_env("S3_BUCKET", "__PLACEHOLDER__"),
        S3_PREFIX=_env("S3_PREFIX", "grogblossoms/"),
        S3_REGION=_env("S3_REGION", "us-east-1"),
        AWS_ACCESS_KEY_ID=_env("AWS_ACCESS_KEY_ID"),
        AWS_SECRET_ACCESS_KEY=_env("AWS_SECRET_ACCESS_KEY"),
        SMTP_HOST=_env("SMTP_HOST"),
        SMTP_PORT=int(_env("SMTP_PORT", "587")),
        SMTP_USER=_env("SMTP_USER"),
        SMTP_PASSWORD=_env("SMTP_PASSWORD"),
        SMTP_FROM=_env("SMTP_FROM", "no-reply@grogblossoms.com"),
        CONTACT_EMAIL=_env("CONTACT_EMAIL", "chris@grogblossoms.com"),
        SESSION_COOKIE_SECURE=_bool("SESSION_COOKIE_SECURE", default=(name == "production")),
        TESTING=(name == "testing"),
        DEBUG=(name == "development"),
    )


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Required env var missing: {name}")
    return val
