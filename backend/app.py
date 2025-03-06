import os
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_bcrypt import Bcrypt
from flask_session import Session
import sqlite3
import redis

# Definir la ruta correcta para la carpeta "templates"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Obtiene la ruta de "backend/"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")    # Agrega "templates"

# Template and static folders are defined
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder="static")
bcrypt = Bcrypt(app)
app.secret_key = "cs50"

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


Session(app)
DATABASE = "app.db"


def get_db():
    # Abre una conexión a la db si es que no existe en g
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # Para devolver resultados como diccionarios
    return g.db

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


@app.teardown_appcontext
def close_db(exception):
    #Cierra la conexión a la base de datos si existe en g
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route('/')
def home():
    db = get_db()
   
    # Show decks
    decks = db.execute("SELECT decks.deck_name FROM user_decks JOIN decks ON user_decks.deck_id = decks.id WHERE user_decks.user_id = ?;", (g.user_id,))
    return render_template("index.html", decks=decks)


@app.route("/login", methods=["GET", "POST"])
def login():
    db = get_db()
    session.clear() # Eliminar sesiones previas

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Search user in database
        cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row is None or not bcrypt.check_password_hash(row["hash"], password):
            flash("Invalid username or password")
            return render_template("login.html"), 400

        session["user_id"] = row["id"]
        flash("Welcome back, " + username)
        return redirect ("/")
    
    return render_template("login.html")


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
            flash("Registered! Welcome, " + username)
            return redirect("/")
        
        except sqlite3.IntegrityError:
            flash("Username " + username + " already exists. Try another one.")
            return render_template("register.html"), 400
    
    return render_template("register.html")


@app.route("/register_deck", methods=['GET', 'POST'])
def register_deck():
     # Conexión segura a la base de datos
    db = get_db()

    # Verify if user is logged
    if g.user_id is None:
        flash("You must be logged in to register a deck.")
        return redirect("/login")
    
    # Register deck
    if request.method == "POST":

        # Capture deck name
        deck_name = request.form.get("deck_name")
        if not isinstance(deck_name, str) or not deck_name.strip():
            flash("Deck name missing.")
            return render_template("register_deck.html"), 400
        
        # Register into database
        try:
            with g.db as db:
                cursor = db.execute("INSERT INTO decks (deck_name) VALUES (?)", (deck_name,))
                deck_id = cursor.lastrowid
                
                # Relate deck with user
                db.execute("INSERT INTO user_decks (user_id, deck_id) VALUES (?, ?)", (g.user_id, deck_id))

            # Message to user
            flash("New deck registered: " + deck_name)
            return redirect("/")
        
        except sqlite3.Error:
            flash("Database error")
            return render_template("register.html"), 400

    return render_template("register_deck.html")


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
