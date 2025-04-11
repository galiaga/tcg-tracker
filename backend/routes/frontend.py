from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

frontend_bp = Blueprint("frontend", __name__)

# Helper function to check auth and get login status for templates
def get_auth_status():
    """Checks JWT token and returns user ID and login status."""
    verify_jwt_in_request(optional=True) 
    current_user_id = get_jwt_identity()
    is_logged_in = current_user_id is not None 
    return current_user_id, is_logged_in

@frontend_bp.route("/", methods=["GET"])
def index_page():
    current_user_id, is_logged_in = get_auth_status()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-decks.html", is_logged_in=is_logged_in)

@frontend_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html", is_logged_in=False)

@frontend_bp.route("/matches_history", methods=["GET"])
def matches_history():
    current_user_id, is_logged_in = get_auth_status()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("matches_history.html", is_logged_in=is_logged_in)

@frontend_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html", is_logged_in=False)

@frontend_bp.route("/decks/<deck_id_slug>", methods=["GET"])
def deck_details_page(deck_id_slug):
    current_user_id, is_logged_in = get_auth_status()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("decks/deck_details.html", is_logged_in=is_logged_in, deck_id_slug=deck_id_slug)

@frontend_bp.route("/my-tags", methods=["GET"])
def my_tags_page():
    current_user_id, is_logged_in = get_auth_status()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-tags.html", is_logged_in=is_logged_in)

@frontend_bp.route("/my-decks", methods=["GET"])
def my_decks_page():
    current_user_id, is_logged_in = get_auth_status()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-decks.html", is_logged_in=is_logged_in)