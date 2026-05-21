"""Tiny generic CRUD factory.

Each resource module calls register_crud() with:
  - bp           : the admin blueprint
  - prefix       : URL prefix and template tag, e.g. 'posts'
  - model        : SQLAlchemy model
  - form_cls     : WTForms class
  - list_cols    : list of (header, getter) for the list table
  - order_by     : ordering for the list query
  - exclude      : tuple of operations to skip ('list','new','edit','delete')
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from flask import flash, redirect, render_template, url_for

from app.blueprints.admin import require_admin_group
from app.extensions import db


def register_crud(
    bp,
    *,
    prefix: str,
    label: str,
    model: type,
    form_cls: type,
    list_cols: Iterable[tuple[str, Callable[[Any], Any]]],
    order_by=None,
    after_save: Callable[[Any], None] | None = None,
    exclude: tuple[str, ...] = (),
) -> None:
    list_cols = list(list_cols)

    if "list" not in exclude:
        @bp.get(f"/{prefix}/", endpoint=f"{prefix}_list")
        @require_admin_group
        def _list():
            q = model.query
            if order_by is not None:
                q = q.order_by(order_by)
            items = q.all()
            return render_template(
                "admin/_list.html",
                label=label, prefix=prefix, items=items, cols=list_cols,
            )

    if "new" not in exclude:
        @bp.route(f"/{prefix}/new", methods=("GET", "POST"), endpoint=f"{prefix}_new")
        @require_admin_group
        def _new():
            form = form_cls()
            if form.validate_on_submit():
                obj = model()
                form.populate_obj(obj)
                db.session.add(obj); db.session.commit()
                if after_save: after_save(obj)
                flash(f"{label} created.", "success")
                return redirect(url_for(f"admin.{prefix}_list"))
            return render_template("admin/_form.html",
                                   label=label, prefix=prefix, form=form, mode="new")

    if "edit" not in exclude:
        @bp.route(f"/{prefix}/<int:id>", methods=("GET", "POST"), endpoint=f"{prefix}_edit")
        @require_admin_group
        def _edit(id: int):
            obj = db.session.get(model, id) or _abort_404()
            form = form_cls(obj=obj)
            if form.validate_on_submit():
                form.populate_obj(obj); db.session.commit()
                if after_save: after_save(obj)
                flash(f"{label} updated.", "success")
                return redirect(url_for(f"admin.{prefix}_list"))
            return render_template("admin/_form.html",
                                   label=label, prefix=prefix, form=form, mode="edit",
                                   obj=obj)

    if "delete" not in exclude:
        @bp.post(f"/{prefix}/<int:id>/delete", endpoint=f"{prefix}_delete")
        @require_admin_group
        def _delete(id: int):
            obj = db.session.get(model, id) or _abort_404()
            db.session.delete(obj); db.session.commit()
            flash(f"{label} deleted.", "success")
            return redirect(url_for(f"admin.{prefix}_list"))


def _abort_404():
    from flask import abort
    abort(404)
