from flask import Blueprint, render_template, redirect, url_for, session
from backend import db
from backend.models.user import User
import logging

frontend_bp = Blueprint("frontend", __name__)
logger = logging.getLogger(__name__)

def get_current_user_for_page_load():
    user = None
    is_logged_in = False
    user_id = session.get("user_id")

    if user_id:
        try:
            user = db.session.get(User, user_id)
            if user:
                is_logged_in = True
            else:
                 logger.warning(f"User ID {user_id} from session not found in database. Clearing session.")
                 session.clear() 
                 is_logged_in = False
                 user = None
        except Exception as e:
             logger.error(f"Error fetching user {user_id} from database during session check: {e}", exc_info=True)
             is_logged_in = False
             user = None
    else:
        is_logged_in = False
        user = None

    return user, is_logged_in

# --- Protected Routes ---
    
@frontend_bp.route("/player-performance", methods=["GET"])
def player_performance_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("player-performance.html", is_logged_in=is_logged_in, user=current_user)

@frontend_bp.route("/decks/<deck_id_slug>", methods=["GET"])
def deck_details_page(deck_id_slug):
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("decks/deck_details.html", is_logged_in=is_logged_in, user=current_user, deck_id_slug=deck_id_slug)

@frontend_bp.route("/", methods=["GET"])
def index_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-decks.html", is_logged_in=is_logged_in, user=current_user)

@frontend_bp.route("/matches-history", methods=["GET"])
def matches_history():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("matches-history.html", is_logged_in=is_logged_in, user=current_user)

@frontend_bp.route("/my-decks", methods=["GET"])
def my_decks_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-decks.html", is_logged_in=is_logged_in, user=current_user)

@frontend_bp.route("/my-profile", methods=["GET"])
def profile_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-profile.html", is_logged_in=is_logged_in, user=current_user)

@frontend_bp.route("/my-tags", methods=["GET"])
def my_tags_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-tags.html", is_logged_in=is_logged_in, user=current_user)

# --- Public Routes ---

@frontend_bp.route("/login", methods=["GET"])
def login_page():
    _user, is_logged_in = get_current_user_for_page_load()
    if is_logged_in:
        return redirect(url_for("frontend.index_page")) 
    return render_template("login.html", is_logged_in=False, user=None)

@frontend_bp.route("/register", methods=["GET"])
def register_page():
    _user, is_logged_in = get_current_user_for_page_load()
    if is_logged_in:
        return redirect(url_for("frontend.index_page")) 
    return render_template("register.html", is_logged_in=False, user=None)

@frontend_bp.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    _user, is_logged_in = get_current_user_for_page_load()
    if is_logged_in:
        return redirect(url_for("frontend.index_page")) 
    return render_template("auth/forgot-password.html", is_logged_in=False, user=None)

@frontend_bp.route("/reset-password/<token>", methods=["GET"])
def reset_password_page(token):
    _user, is_logged_in = get_current_user_for_page_load()
    if is_logged_in:
        return redirect(url_for("frontend.index_page")) 
    return render_template('auth/reset-password.html', token=token, is_logged_in=False, user=None)
