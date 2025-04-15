from flask import Blueprint, request, jsonify, current_app, session
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from backend import db
from backend.models.user import User
from backend.services.user_service import get_user_by_username
from backend.utils.decorators import login_required

import secrets

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()

def create_user(username, password):
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(username=username, hash=hashed_password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user.id
    except IntegrityError:
        db.session.rollback()
        return {"error": "Username already exists", "type": "DUPLICATE_USERNAME"}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": f"Unexpected error: {str(e)}", "type": "UNKNOWN_ERROR"}, 400

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    confirmation = data.get("confirmation")

    if not username or not password or not confirmation:
        return jsonify({"error": "All fields are required"}), 400
    if password != confirmation:
        return jsonify({"error": "Passwords do not match."}), 400

    user_id_or_error = create_user(username, password)

    if isinstance(user_id_or_error, tuple):
        error_response, status_code = user_id_or_error
        return jsonify(error_response), status_code

    user_id = user_id_or_error
    session.clear() 
    session['user_id'] = user_id
    session['username'] = username
    if 'csrf_token' not in session:
         session['csrf_token'] = secrets.token_hex(16)
    session.permanent = True 

    response_data = {
        "username": username,
        "message": f"User {username} successfully registered and logged in."
    }
    return jsonify(response_data), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = get_user_by_username(username)
    if user and bcrypt.check_password_hash(user.hash, password):
        session.clear() 
        session['user_id'] = user.id
        session['username'] = user.username
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(16)
        session.permanent = True 

        print(f"DEBUG LOGIN: Session established for user {user.id}, username {user.username}")
        print(f"DEBUG LOGIN: Session CSRF Token: {session['csrf_token']}")
        print(f"DEBUG LOGIN: Session ID (in cookie): {request.cookies.get('session')}") 

        response_data = {
            "username": user.username,
            "message": "Login successful"
        }
        return jsonify(response_data), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    user_id = session.get('user_id')
    session.clear()
    print(f"DEBUG LOGOUT: Session cleared for potential user {user_id}")
    response = jsonify({"message": "Logout successful"})
    return response, 200

@auth_bp.route("/csrf_token", methods=["GET"])
def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(16)
        session['csrf_token'] = token
        print("WARN: CSRF token requested but none found in session; generated new one.")

    if not session.get("user_id"):
         return jsonify({"error": "Not authenticated"}), 401

    return jsonify({"csrf_token": token}), 200

@auth_bp.route("/profile", methods=["GET"])
@login_required 
def profile():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return jsonify({"error": "User data not found, session cleared"}), 404
    return jsonify({"id": user.id, "username": session.get('username', user.username)}), 200