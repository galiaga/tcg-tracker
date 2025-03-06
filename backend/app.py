import os
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_bcrypt import Bcrypt
import sqlite3

# Definir la ruta correcta para la carpeta "templates"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Obtiene la ruta de "backend/"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")    # Agrega "templates"

# Template and static folders are defined
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder="static")
bcrypt = Bcrypt(app)
app.secret_key = "cs50"

print("Flask-Bcrypt está funcionando correctamente")

DATABASE = "app.db"

def get_db():
    # Abre una conexión a la db si es que no existe en g
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # Para devolver resultados como diccionarios
    return g.db

@app.teardown_appcontext
def close_db(exception):
    #Cierra la conexión a la base de datos si existe en g
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    db = get_db()
    # Solo para mostrar que funciona
    flash("Database connected!")

    return render_template("index.html")


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
        hashed_password  = bcrypt.generate_password_hash("password").decode("utf-8")

        # Register into database
        try:
            with g.db as db:
                db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed_password))
            
            # Message to user
            flash("Registered! Welcome, " + username)
            return redirect("/")
        
        except sqlite3.IntegrityError:
            flash("Username " + username + " already exists.")
            return render_template("register.html"), 400
    
    return render_template("register.html")

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
