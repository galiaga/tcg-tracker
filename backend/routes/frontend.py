from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from jwt.exceptions import ExpiredSignatureError 
from backend import db
from backend.models.user import User

frontend_bp = Blueprint("frontend", __name__)

def get_current_user_for_page_load():
    user = None
    is_logged_in = False
    current_user_id = None
    try:
        try:
            verify_jwt_in_request(optional=True)
        except ExpiredSignatureError:
            print("DEBUG: Expired signature detected during optional verify on page load.")
            pass 
        except Exception as e:
            print(f"DEBUG: Other JWT error during optional verify on page load: {e}")
            pass

        current_user_id = get_jwt_identity() 

        if current_user_id:
            user = db.session.get(User, current_user_id)
            if user:
                is_logged_in = True
            else:
                 print(f"WARNING: User ID {current_user_id} from JWT not found in database.")
                 is_logged_in = False
        else:
            is_logged_in = False
    except Exception as e:
        print(f"ERROR during get_current_user_for_page_load: {e}")
        is_logged_in = False
        user = None
    return user, is_logged_in

# --- Protected Routes ---

@frontend_bp.route("/", methods=["GET"])
def index_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-decks.html", is_logged_in=is_logged_in, user=current_user)

@frontend_bp.route("/matches_history", methods=["GET"])
def matches_history():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("matches_history.html", is_logged_in=is_logged_in, user=current_user)

@frontend_bp.route("/decks/<deck_id_slug>", methods=["GET"])
def deck_details_page(deck_id_slug):
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("decks/deck_details.html", is_logged_in=is_logged_in, user=current_user, deck_id_slug=deck_id_slug)

@frontend_bp.route("/my-tags", methods=["GET"])
def my_tags_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-tags.html", is_logged_in=is_logged_in, user=current_user) 

@frontend_bp.route("/my-decks", methods=["GET"])
def my_decks_page():
    current_user, is_logged_in = get_current_user_for_page_load()
    if not is_logged_in:
        return redirect(url_for("frontend.login_page"))
    return render_template("my-decks.html", is_logged_in=is_logged_in, user=current_user)

# --- Public Routes ---

@frontend_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html", is_logged_in=False, user=None)

@frontend_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html", is_logged_in=False, user=None)