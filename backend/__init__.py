import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
import click

db = SQLAlchemy(session_options={"autocommit": False, "autoflush": False})
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name=None):
    """Flask application factory."""
    app = Flask(__name__, instance_relative_config=False)

    flask_env = os.environ.get('FLASK_ENV', os.environ.get('NODE_ENV', 'development'))
    is_production = (flask_env == 'production')

    print(f"INFO: Loading {'Production' if is_production else 'Development'} Configuration")
    app.config['DEBUG'] = not is_production

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

    flask_secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not flask_secret_key:
        if is_production:
            raise ValueError("FATAL: FLASK_SECRET_KEY environment variable not set in production environment")
        else:
            print("WARNING: FLASK_SECRET_KEY not set. Using default insecure key for development.")
            flask_secret_key = 'dev-insecure-flask-key-replace-in-dotenv' 
    app.config['SECRET_KEY'] = flask_secret_key 

    jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret_key:
        if is_production:
            raise ValueError("FATAL: JWT_SECRET_KEY environment variable not set in production environment")
        else:
            print("WARNING: JWT_SECRET_KEY not set. Using default insecure key for development.")
            jwt_secret_key = 'dev-insecure-jwt-key-replace-in-dotenv' 
    app.config['JWT_SECRET_KEY'] = jwt_secret_key

    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=int(os.environ.get('JWT_ACCESS_MINUTES', 1)))
    print(f"WARNING: JWT_ACCESS_TOKEN_EXPIRES set to 1 minute for testing!")
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=int(os.environ.get('JWT_REFRESH_DAYS', 7)))

    app.config["JWT_COOKIE_SECURE"] = not app.config['DEBUG']
    app.config["JWT_HTTPONLY"] = True
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
    app.config["JWT_REFRESH_COOKIE_PATH"] = "/"

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    try:
        from backend.routes import register_routes
        register_routes(app)
        print("INFO: Routes registered successfully.")
    except ImportError as e:
        print(f"ERROR: Could not import or register routes: {e}")

    try:
        from manage import seed_deck_types, update_commanders_data, update_flags

        app.cli.add_command(seed_deck_types, name='seed-deck-types')
        app.cli.add_command(update_commanders_data, name='update-commanders')
        app.cli.add_command(update_flags, name='update-flags')
        print("INFO: Custom CLI commands registered successfully.")

    except ImportError as e:
        print(f"ERROR: Could not import or register custom CLI commands from manage.py: {e}")
        print("INFO: Ensure manage.py is in the project root or adjust import path.")

    return app