from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from backend.database import get_db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/login", methods=["POST"])
def login():
    db = get_db()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Search user in database
    user = db.execute("SELECT id, hash FROM users WHERE username = ?", (username,)).fetchone()

     # Verify if user exists
    if not user or not bcrypt.check_password_hash(user["hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Generate JWT token
    access_token = create_access_token(identity=str(user["id"]))
    
    return jsonify({"access_token": access_token}), 200