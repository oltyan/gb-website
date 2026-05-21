"""HTTP client for the mm-sporekles sidecar uploader.

The sidecar (Fastify, mm-sporekles repo `api/src/routes/assets.ts`) is the
single write path into the per-tenant S3 bucket. It handles content-type
sniffing, manifest.json regen, and CloudFront invalidation. Gb-website
forwards the admin's identity via the same X-Auth-Request-* headers that
mm-mycelium-gateway injects upstream — the sidecar isn't reachable from
outside the shared-tunnel Docker network, so the network is the trust
boundary.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import BinaryIO

import requests
from flask import current_app

from app.extensions import db
from app.models import Asset


class SporeklesError(RuntimeError):
    """Raised when the sidecar refuses an upload or is unreachable."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class AuthContext:
    email: str
    user: str
    groups: list[str]

    def headers(self) -> dict[str, str]:
        return {
            "X-Auth-Request-Email": self.email,
            "X-Auth-Request-User": self.user,
            "X-Auth-Request-Groups": ",".join(self.groups),
        }


class SporeklesClient:
    def __init__(
        self,
        api_base: str,
        tenant: str,
        get_auth: Callable[[], AuthContext],
        *,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ):
        self.api_base = api_base.rstrip("/")
        self.tenant = tenant
        self._get_auth = get_auth
        self._timeout = timeout
        self._session = session or requests.Session()

    def upload_asset(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str,
        *,
        caption: str | None = None,
    ) -> Asset:
        url = f"{self.api_base}/{self.tenant}/assets"
        files = {"file": (filename, file_obj, content_type)}
        headers = self._get_auth().headers()

        try:
            resp = self._session.post(url, files=files, headers=headers, timeout=self._timeout)
        except requests.RequestException as exc:
            raise SporeklesError(f"sporekles unreachable: {exc}") from exc

        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("error") or resp.text
            except ValueError:
                msg = resp.text or f"HTTP {resp.status_code}"
            raise SporeklesError(msg, status_code=resp.status_code)

        try:
            body = resp.json()
        except ValueError as exc:
            raise SporeklesError(f"sporekles returned non-JSON: {resp.text!r}") from exc

        entry = body.get("entry")
        if not entry:
            raise SporeklesError(f"sporekles response missing entry: {body!r}")

        # Sidecar key prefix mirrors the URL category path: /<tenant>/assets -> assets/<filename>
        key = f"assets/{entry['filename']}"
        asset = Asset(
            key=key,
            url=entry["url"],
            filename=entry["filename"],
            content_type=entry.get("contentType", content_type),
            size_bytes=entry.get("bytes", 0),
            caption=caption or None,
        )
        db.session.add(asset)
        db.session.commit()
        return asset


def get_client() -> SporeklesClient:
    """Build a SporeklesClient configured from the current app + session."""
    from flask_login import current_user

    api_base = current_app.config["SPOREKLES_API_BASE"]
    tenant = current_app.config["SPOREKLES_TENANT"]

    def _auth() -> AuthContext:
        if not getattr(current_user, "is_authenticated", False):
            raise SporeklesError("upload requires an authenticated admin")
        return AuthContext(
            email=current_user.email or "",
            user=current_user.display_name or current_user.email or "",
            groups=list(current_user.groups or []),
        )

    return SporeklesClient(api_base=api_base, tenant=tenant, get_auth=_auth)
