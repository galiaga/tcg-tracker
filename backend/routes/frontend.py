from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route("/", methods=["GET"])
def index_page():
    return render_template("index.html")

@frontend_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@frontend_bp.route("/log_match", methods=["GET"])
def log_match_page():
    return render_template("log_match.html")

@frontend_bp.route("/matches_history", methods=["GET"])
def matches_history():
    return render_template("matches_history.html")

@frontend_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@frontend_bp.route("/my-decks", methods=["GET"])
def register_deck_page():
    return render_template("my-decks.html")