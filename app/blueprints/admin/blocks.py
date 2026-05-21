"""HTMX endpoints for the post block editor."""
import json

from flask import abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Post
from app.services.blocks import BLOCK_TYPES, normalize_blocks
from . import bp, require_admin_group


@bp.get("/blocks/new/<block_type>", endpoint="blocks_new_partial")
@require_admin_group
def blocks_new_partial(block_type: str):
    if block_type not in BLOCK_TYPES:
        abort(404)
    import secrets
    return render_template(
        f"admin/_blocks/{block_type}_form.html",
        block={"id": f"blk_{secrets.token_hex(6)}", "type": block_type, "data": {}},
    )


@bp.post("/posts/<int:id>/blocks/save", endpoint="posts_blocks_save")
@require_admin_group
def posts_blocks_save(id: int):
    post = db.session.get(Post, id) or abort(404)
    raw = request.form.get("blocks") or "[]"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        flash("Invalid blocks JSON.", "error")
        return redirect(url_for("admin.posts_edit", id=id))
    post.blocks = normalize_blocks(parsed, strict=False)
    db.session.commit()
    flash("Blocks saved.", "success")
    return redirect(url_for("admin.posts_edit", id=id))
