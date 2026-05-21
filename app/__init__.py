import os
from dataclasses import asdict

from flask import Flask, jsonify

from .config import load_config
from .extensions import csrf, db, login_manager, migrate, oauth


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "production")
    app = Flask(__name__)
    cfg = load_config(config_name)
    app.config.update(asdict(cfg))

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    login_manager.login_view = "auth.login"

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    from .blueprints.public import bp as public_bp

    app.register_blueprint(public_bp)

    if app.config.get("OIDC_DISCOVERY_URL"):
        oauth.register(
            name="fa",
            client_id=app.config["OIDC_CLIENT_ID"],
            client_secret=app.config["OIDC_CLIENT_SECRET"],
            server_metadata_url=app.config["OIDC_DISCOVERY_URL"],
            client_kwargs={"scope": "openid email profile groups"},
        )

    from .blueprints.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from .blueprints.admin import bp as admin_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.template_global()
    def safe_url(endpoint, **values):
        try:
            from flask import url_for

            return url_for(endpoint, **values)
        except Exception:
            return "#"

    import markdown as md

    @app.template_filter("markdown")
    def _markdown_filter(text: str) -> str:
        if not text:
            return ""
        return md.markdown(text, extensions=["fenced_code", "tables", "nl2br"])

    import re

    @app.template_filter("pencil_highlight")
    def _pencil(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"==(.+?)==", r'<span class="bg-accent-amber/20 px-0.5">\1</span>', text)

    from .models import Gallery as _Gallery

    @app.template_global("get_gallery")
    def _get_gallery(gid: int):
        return db.session.get(_Gallery, gid)

    return app
