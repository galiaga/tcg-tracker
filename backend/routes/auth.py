# backend/routes/auth.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, create_refresh_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
)
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError

from backend import db
from backend.models.user import User
from backend.services.user_service import get_user_by_username

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
    access_token = create_access_token(identity=str(user_id))

    response_data = {
        "username": username,
        "message": f"User {username} successfully registered."
    }
    response = jsonify(response_data)
    set_access_cookies(response, access_token)
    return response, 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = get_user_by_username(username)
    if user and bcrypt.check_password_hash(user.hash, password):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        response_data = {
            "username": user.username,
            "message": "Login successful"
        }
        response = jsonify(response_data)
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response, 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    return response, 200

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "username": user.username}), 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    response = jsonify({"message": "Access token refreshed successfully"})
    set_access_cookies(response, new_access_token)
    return response, 200