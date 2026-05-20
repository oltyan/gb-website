import os
from flask import Flask, jsonify
from dataclasses import asdict
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

    return app
