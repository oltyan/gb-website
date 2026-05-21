import pytest
from app.services.blocks import BLOCK_TYPES, normalize_blocks, validate_block


def test_known_block_types():
    assert set(BLOCK_TYPES) == {
        "paragraph", "heading", "image", "pull_quote",
        "gallery_inline", "divider", "callout", "stat_pair", "bento_card",
    }


def test_validate_paragraph_ok():
    block = {"type": "paragraph", "id": "blk1", "data": {"markdown": "hello"}}
    validate_block(block)  # no raise


def test_validate_unknown_type_raises():
    with pytest.raises(ValueError):
        validate_block({"type": "unknown", "id": "x", "data": {}})


def test_validate_image_requires_url():
    with pytest.raises(ValueError):
        validate_block({"type": "image", "id": "x", "data": {"alt": "x"}})


def test_validate_heading_level_range():
    validate_block({"type": "heading", "id": "x", "data": {"level": 2, "text": "h"}})
    with pytest.raises(ValueError):
        validate_block({"type": "heading", "id": "x", "data": {"level": 5, "text": "h"}})


def test_normalize_blocks_assigns_ids():
    raw = [{"type": "paragraph", "data": {"markdown": "x"}}]
    out = normalize_blocks(raw)
    assert out[0]["id"]


def test_normalize_blocks_filters_invalid():
    raw = [
        {"type": "paragraph", "data": {"markdown": "x"}},
        {"type": "bogus", "data": {}},
    ]
    out = normalize_blocks(raw, strict=False)
    assert len(out) == 1


def test_normalize_blocks_strict_raises():
    raw = [{"type": "bogus", "data": {}}]
    with pytest.raises(ValueError):
        normalize_blocks(raw, strict=True)
