import os
from flask import Flask, flash, redirect, render_template, request, session, g, jsonify
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_jwt_extended import JWTManager
from datetime import timedelta

from backend.database import get_db, close_db
from backend.routes.auth import auth_bp
from backend.routes.frontend import frontend_bp
from backend.routes.matches import matches_bp
from backend.routes.decks import decks_bp

import sqlite3
import redis

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

app.teardown_appcontext(close_db)
app.register_blueprint(auth_bp)
app.register_blueprint(frontend_bp)
app.register_blueprint(matches_bp)
app.register_blueprint(decks_bp)

# Habilita el modo debug
app.config["DEBUG"] = True

# Configure Flask-Session to use Redis Cloud
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

# Connect Flask-Session to Redis Cloud
app.config["SESSION_REDIS"] = redis.Redis(
    host="redis-10755.c10.us-east-1-2.ec2.redns.redis-cloud.com",  # Tu host de Redis
    port=10755,  # Tu puerto de Redis
    password="NzMhEx6py7O86SM08REwFNVr78HopchP",  # Sustituye con la contraseña real de Redis Cloud
    ssl=False  # Usa SSL para conexiones seguras
)


# Value mapping
RESULT_MAPPING = {0: "Lose", 1: "Win", 2: "Draw"}

Session(app)

# To show username across the app
@app.before_request
def load_logged_in_user():
    g.db = get_db()
    
    # Load logged user username
    user_id = session.get("user_id")

    if user_id is None:
        g.username = None
        g.user_id = None
    else:
        row = g.db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
        
        if row:        
            g.username = row["username"] if row else None # Saves username in g.username
            g.user_id = row["id"] if row else None # Saves id in g.user_id
        else:
            g.username = None
            g.user_id = None


@app.context_processor
def inject_user():
    # Makes the username available for all templates
    return {"username": g.username}


@app.route('/')
def home():
    db = get_db()
   
    # Show decks
    decks = db.execute("SELECT decks.deck_name FROM user_decks JOIN decks ON user_decks.deck_id = decks.id WHERE user_decks.user_id = ?;", (g.user_id,))
    return render_template("index.html", decks=decks)


@app.route("/logout")
    # Log user out
def logout():
    
    # Forgets any user_id
    session.clear()

    # Redirects to login form
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def add_user():
    # Conexión segura a la base de datos
    db = get_db()

    # Register user
    if request.method == "POST":

        # Capture username
        username = request.form.get("username")
        if not isinstance(username, str) or not username:
            flash("Username missing.")
            return render_template("register.html"), 400
        
        # Capture password
        password = request.form.get("password")
        if not isinstance(password, str) or not password:
            flash("Password missing.")
            return render_template("register.html"), 400
        
        # Capture confirmation
        confirmation = request.form.get("confirmation")
        if not isinstance(confirmation, str) or not confirmation:
            flash("Confirmation missing.")
            return render_template("register.html"), 400
        
        # Confirmation == Password
        elif (confirmation != password):
            flash("Passwords don't match.")
            return render_template("register.html"), 400 
        
        # Hash the password
        hashed_password  = bcrypt.generate_password_hash(password).decode("utf-8")

        # Register into database
        try:
            with g.db as db:
                cursor = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed_password))
                session["user_id"] = cursor.lastrowid

            # Message to user
            flash("Registered! Welcome, " + username, "success")
            return redirect("/")
        
        except sqlite3.IntegrityError:
            flash("Username " + username + " already exists. Try another one.")
            return render_template("register.html"), 400
    
    return render_template("register.html")


@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"error": "Missing or invalid token"}), 401


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
