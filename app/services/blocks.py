"""Block schema validation + normalization.

Each block: { "id": str, "type": str, "data": dict }
"""
from __future__ import annotations

import secrets
from typing import Any


def _validate_paragraph(d: dict) -> None:
    if "markdown" not in d:
        raise ValueError("paragraph requires 'markdown'")


def _validate_heading(d: dict) -> None:
    level = d.get("level")
    if level not in (2, 3, 4):
        raise ValueError("heading 'level' must be 2, 3, or 4")
    if not d.get("text"):
        raise ValueError("heading requires 'text'")


def _validate_image(d: dict) -> None:
    if not d.get("url"):
        raise ValueError("image requires 'url'")
    if d.get("tilt") not in (None, -2, -1, 0, 1, 2):
        raise ValueError("image 'tilt' must be -2..2")
    if d.get("border") not in (None, "white", "amber", "red"):
        raise ValueError("image 'border' must be white|amber|red")


def _validate_pull_quote(d: dict) -> None:
    if not d.get("text"):
        raise ValueError("pull_quote requires 'text'")
    if d.get("style") not in (None, "torn", "amber-bar"):
        raise ValueError("pull_quote 'style' must be torn|amber-bar")


def _validate_gallery_inline(d: dict) -> None:
    if not isinstance(d.get("gallery_id"), int):
        raise ValueError("gallery_inline requires int 'gallery_id'")


def _validate_divider(d: dict) -> None:
    if d.get("style") not in (None, "torn", "dashed-amber", "sketch-line"):
        raise ValueError("divider 'style' invalid")


def _validate_callout(d: dict) -> None:
    if not d.get("text") or not d.get("label"):
        raise ValueError("callout requires 'label' and 'text'")
    if d.get("accent") not in (None, "red", "amber"):
        raise ValueError("callout 'accent' must be red|amber")


def _validate_stat_pair(d: dict) -> None:
    for side in ("left", "right"):
        s = d.get(side) or {}
        if not s.get("value") or not s.get("label"):
            raise ValueError(f"stat_pair.{side} requires value+label")


def _validate_bento_card(d: dict) -> None:
    if not d.get("title") or not d.get("body"):
        raise ValueError("bento_card requires title+body")


BLOCK_TYPES: dict[str, Any] = {
    "paragraph": _validate_paragraph,
    "heading": _validate_heading,
    "image": _validate_image,
    "pull_quote": _validate_pull_quote,
    "gallery_inline": _validate_gallery_inline,
    "divider": _validate_divider,
    "callout": _validate_callout,
    "stat_pair": _validate_stat_pair,
    "bento_card": _validate_bento_card,
}


def validate_block(block: dict) -> None:
    if not isinstance(block, dict):
        raise ValueError("block must be a dict")
    t = block.get("type")
    if t not in BLOCK_TYPES:
        raise ValueError(f"unknown block type: {t!r}")
    data = block.get("data") or {}
    if not isinstance(data, dict):
        raise ValueError("block 'data' must be a dict")
    BLOCK_TYPES[t](data)


def normalize_blocks(raw: list[dict], *, strict: bool = False) -> list[dict]:
    out: list[dict] = []
    for b in raw or []:
        try:
            validate_block(b)
        except ValueError:
            if strict:
                raise
            continue
        bid = b.get("id") or f"blk_{secrets.token_hex(8)}"
        out.append({"id": bid, "type": b["type"], "data": b.get("data") or {}})
    return out
