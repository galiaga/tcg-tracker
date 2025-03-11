from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from backend.database import get_db
from flask_bcrypt import Bcrypt
import sqlite3

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()

@auth_bp.route("/register", methods=["POST"])
def register():
    db = get_db()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    confirmation = data.get("confirmation")
        
    if not username or not password or not confirmation:
        return jsonify({"error": "All fields are required"}), 400
    
    if confirmation != password:
        return jsonify({"error": "Passwords do not match."}), 401

    hashed_password  = bcrypt.generate_password_hash(password).decode("utf-8")

    try:
        cursor = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed_password))
        db.commit()
        user_id = cursor.lastrowid

        # Generate JWT
        access_token = create_access_token(identity=str(user_id))
        return jsonify({"access_token": access_token, "username": username}), 201

    
    except sqlite3.IntegrityError:
        return jsonify({"error": f"Username {username} already exists. Try another one."}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    db = get_db()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Search user in database
    row = db.execute("SELECT id, username, hash FROM users WHERE username = ?", (username,)).fetchone()

    if row and bcrypt.check_password_hash(row["hash"], password):
            access_token = create_access_token(identity=str(row["id"]))
            return jsonify({"access_token": access_token, "username": row["username"]}), 200

    else:
        return jsonify({"error": "Invalid username or password"}), 401


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user = get_jwt_identity()  # Obtiene el usuario autenticado desde el token
    return jsonify({"user": user}), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({"access_token": new_access_token})