"""S3 uploader to mm-sporekles' design-assets bucket.

v1: PLACEHOLDER implementation. Real boto3 wiring lands once the
mm-grogblossoms-uploader IAM user is provisioned (see spec, "Image flow").

Until then, the admin asset picker uses the `register_url()` path: paste a
CDN URL of a file you've already placed in the bucket via other means.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from flask import current_app

from app.extensions import db
from app.models import Asset


class UploaderNotProvisioned(RuntimeError):
    pass


@dataclass
class UploadResult:
    asset: Asset


def upload(file_obj: BinaryIO, filename: str, content_type: str) -> UploadResult:
    """Stream a file to S3, persist an Asset row, return both."""
    bucket = current_app.config.get("S3_BUCKET", "__PLACEHOLDER__")
    if bucket.startswith("__PLACEHOLDER__"):
        raise UploaderNotProvisioned(
            "S3 uploader is not yet provisioned. Use the 'Paste CDN URL' flow "
            "in /admin/assets/ until mm-sporekles infra exposes the uploader."
        )
    # When the real implementation lands:
    #   import boto3
    #   key = f"{current_app.config['S3_PREFIX']}{_safe_name(filename)}"
    #   s3 = boto3.client('s3', region_name=current_app.config['S3_REGION'])
    #   s3.upload_fileobj(file_obj, bucket, key,
    #       ExtraArgs={'ContentType': content_type,
    #                  'CacheControl': 'public, max-age=31536000, immutable'})
    #   url = current_app.config['CDN_BASE_URL'].rstrip('/') + '/' + key
    #   asset = Asset(key=key, url=url, filename=filename, content_type=content_type, size_bytes=…)
    #   db.session.add(asset); db.session.commit()
    #   return UploadResult(asset=asset)
    raise UploaderNotProvisioned("Real uploader implementation pending.")


def register_url(public_url: str, *, caption: str = "") -> Asset:
    """Record an externally-uploaded CDN URL as an Asset row.

    The URL is expected to be under CDN_BASE_URL + S3_PREFIX.
    """
    cdn = current_app.config["CDN_BASE_URL"].rstrip("/") + "/"
    prefix = current_app.config["S3_PREFIX"]
    if not public_url.startswith(cdn + prefix):
        raise ValueError(f"URL must start with {cdn}{prefix}")
    key = public_url[len(cdn):]
    filename = key.rsplit("/", 1)[-1]
    asset = Asset(
        key=key, url=public_url, filename=filename,
        content_type="application/octet-stream", size_bytes=0,
        caption=caption or None,
    )
    db.session.add(asset); db.session.commit()
    return asset
