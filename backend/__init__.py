import os
from flask import Flask, jsonify, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta
from flask_session import Session
import click, logging, secrets


# Initialize extensions top-level
db = SQLAlchemy(session_options={"autocommit": False, "autoflush": False})
migrate = Migrate()
server_session = Session()

def create_app(config_name=None):
    """Flask application factory."""
    app = Flask(__name__, instance_relative_config=False)

    # --- Configuration Loading ---
    flask_env = os.environ.get('FLASK_ENV', os.environ.get('NODE_ENV', 'development'))
    is_production = (flask_env == 'production')
    print(f"INFO: Loading {'Production' if is_production else 'Development'} Configuration")
    app.config['DEBUG'] = not is_production

    # Database Config
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        if is_production:
             raise ValueError("FATAL: DATABASE_URL environment variable not set in production environment")
        print("WARNING: DATABASE_URL environment variable not set. Using local SQLite 'backend/app.db'.")
        backend_folder_path = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(backend_folder_path, 'app.db')
        database_url = f"sqlite:///{db_path}"
    elif database_url.startswith('postgres://'):
         database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Secret Keys
    flask_secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-insecure-flask-key-replace-in-dotenv' if not is_production else None)
    if not flask_secret_key: raise ValueError("FATAL: FLASK_SECRET_KEY environment variable not set in production environment")
    if flask_secret_key == 'dev-insecure-flask-key-replace-in-dotenv': print("WARNING: Using default insecure FLASK_SECRET_KEY.")
    app.config['SECRET_KEY'] = flask_secret_key

    # Flask-Session Configuration
    app.config['SESSION_TYPE'] = 'sqlalchemy' # Use SQLAlchemy backend
    app.config['SESSION_SQLALCHEMY'] = db      # Use the existing db instance
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'sessions' # Name of the session table
    app.config['SESSION_PERMANENT'] = True     # Make sessions permanent (use lifetime)
    app.config['SESSION_KEY_PREFIX'] = 'session:' # Prefix for keys in db (optional)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7)))
    # Cookie settings
    app.config['SESSION_COOKIE_SECURE'] = is_production # True in prod (HTTPS), False in dev
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Crucial for security
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Good default ('Strict' is more secure but can break some cross-origin links)

    # --- Initialize Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    server_session.init_app(app)

    @app.before_request
    def generate_csrf_token():
        # Generate a token if one doesn't exist in the session
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(16)
    
    # --- Register Blueprints ---
    try:
        from backend.routes import register_routes
        register_routes(app)
        print("INFO: Routes registered successfully.")
    except ImportError as e:
        print(f"ERROR: Could not import or register routes: {e}")

    # --- Register Custom CLI Commands ---
    try:
        from manage import seed_deck_types, update_commanders_data, update_flags
        app.cli.add_command(seed_deck_types, name='seed-deck-types')
        app.cli.add_command(update_commanders_data, name='update-commanders')
        app.cli.add_command(update_flags, name='update-flags')
        print("INFO: Custom CLI commands registered successfully.")
    except ImportError as e:
        print(f"ERROR: Could not import or register custom CLI commands from manage.py: {e}")
        print("INFO: Ensure manage.py is in the project root or adjust import path.")

    @app.cli.command("create-session-table")
    def create_session_table():
        """Creates the session table in the database."""
        with app.app_context():
            # This creates the table based on SESSION_SQLALCHEMY_TABLE config
            server_session.app.session_interface.db.create_all()
            print(f"Session table '{app.config['SESSION_SQLALCHEMY_TABLE']}' created (if it didn't exist).")

    return app