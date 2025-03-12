import os
from datetime import timedelta
from flask import jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from backend import create_app

app = create_app()


bcrypt = Bcrypt(app)
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Update when in PROD
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)  # 🔹 Access Token dura 15 min
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)  # 🔹 Refresh Token dura 7 días
jwt = JWTManager(app)

app.secret_key = "cs50"

RESULT_MAPPING = {0: "Lose", 1: "Win", 2: "Draw"}

@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"error": "Missing or invalid token"}), 401

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the API"}), 200

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)