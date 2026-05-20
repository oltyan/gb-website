from flask import Blueprint, render_template

bp = Blueprint("public", __name__)


@bp.get("/")
def home():
    return render_template("public/home.html")


@bp.get("/log")
def log_index():
    return "Ship's Log (placeholder)"


@bp.get("/manifest")
def manifest():
    return "Manifest (placeholder)"


@bp.get("/crew")
def crew():
    return "Crew (placeholder)"


@bp.get("/booty")
def booty():
    return "Booty (placeholder)"


@bp.get("/crows-nest")
def crows_nest():
    return "Crow's Nest (placeholder)"
