from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError

from backend import db
from backend.models.user import User
from backend.services.user_service import get_user_by_username

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()

# Create a new user with a hashed password and store in DB
def create_user(username, password):
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(username=username, hash=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user.id
    except IntegrityError as e:
        db.session.rollback()
        return {"error": "Username already exists", "type": "DUPLICATE_USERNAME"}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": f"Unexpected error: {str(e)}", "type": "UNKNOWN_ERROR"}, 400

# Register a new user 
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username, password, confirmation = data.get("username"), data.get("password"), data.get("confirmation")
        
    if not username or not password or not confirmation:
        return jsonify({"error": "All fields are required"}), 400
    
    if password != confirmation:
        return jsonify({"error": "Passwords do not match."}), 400
    
    user_id = create_user(username, password)

    if isinstance(user_id, tuple):  # Esto significa que devolvió (error, código)
        error_response, status_code = user_id
        return jsonify(error_response), status_code 
    
    access_token = create_access_token(identity=str(user_id))
    return jsonify({
        "access_token": access_token,
        "username": username,
        "message": f"User {username} successfully registered."
    }), 201
    
# Authenticate user and return JWT tokens
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username, password = data.get("username"), data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = get_user_by_username(username)
    if user and bcrypt.check_password_hash(user.hash, password):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify ({"access_token": access_token, "refresh_token": refresh_token, "username": user.username}), 200

    return jsonify({"error": "Invalid username or password"}), 401

# Retrieve user profile (protected route)
@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"id": user.id, "username": user.username}), 200

# Generate a new access token using the refresh token
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({"access_token": new_access_token}), 200