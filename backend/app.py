import os
from flask import Flask, flash, redirect, render_template, request, session, g, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from datetime import timedelta

from backend.database import get_db, close_db
from backend.routes.auth import auth_bp
from backend.routes.frontend import frontend_bp
from backend.routes.matches import matches_bp
from backend.routes.decks import decks_bp

# Definir la ruta correcta para la carpeta "templates"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Obtiene la ruta de "backend/"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")    # Agrega "templates"

# Template and static folders are defined
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder="static")
bcrypt = Bcrypt(app)

app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Update when in PROD
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)  # 🔹 Access Token lasts 15 min
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)  # 🔹 Refresh Token lasts 7 days
jwt = JWTManager(app)

app.secret_key = "cs50"

app.register_blueprint(auth_bp)
app.register_blueprint(frontend_bp)
app.register_blueprint(matches_bp)
app.register_blueprint(decks_bp)

app.teardown_appcontext(close_db)

# Habilita el modo debug
app.config["DEBUG"] = True

# Value mapping
RESULT_MAPPING = {0: "Lose", 1: "Win", 2: "Draw"}

@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"error": "Missing or invalid token"}), 401

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the API"}), 200

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
