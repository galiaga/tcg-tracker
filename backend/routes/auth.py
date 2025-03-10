from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from backend.database import get_db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/login", methods=["POST"])
def login():
    db = get_db()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Search user in database
    user = db.execute("SELECT id, username, hash FROM users WHERE username = ?", (username,)).fetchone()

     # Verify if user exists
    if not user or not bcrypt.check_password_hash(user["hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Convert `sqlite3.Row` to dict
    user_dict = dict(user)
    
    # Generate JWT token
    access_token = create_access_token(identity=str(user["id"]))
    
    return jsonify({
        "access_token": access_token,
        "username": user["username"]
        }), 200