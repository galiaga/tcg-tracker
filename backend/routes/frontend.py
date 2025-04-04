from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route("/", methods=["GET"])
def index_page():
    return render_template("index.html")

@frontend_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@frontend_bp.route("/matches_history", methods=["GET"])
def matches_history():
    return render_template("matches_history.html")

@frontend_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@frontend_bp.route("/my-decks", methods=["GET"])
def register_deck_page():
    return render_template("my-decks.html")

@frontend_bp.route("/decks/<deck_id_slug>", methods=["GET"])
def deck_details_page(deck_id_slug):
    return render_template("decks/deck_details.html")
