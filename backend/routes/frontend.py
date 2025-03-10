from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@frontend_bp.route("/log_match", methods=["GET"])
def log_match_page():
    return render_template("log_match.html")

@frontend_bp.route("/register_deck", methods=["GET"])
def register_deck_page():
    return render_template("register_deck.html")