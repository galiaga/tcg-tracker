# backend/__init__.py

# --- Imports ---
import os
from flask import Flask, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta, date
from flask_session import Session
import secrets
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail
from dotenv import load_dotenv

# --- Extension Initialization ---
db = SQLAlchemy(session_options={"autocommit": False, "autoflush": False})
migrate = Migrate()
server_session = Session()
limiter = Limiter(key_func=get_remote_address)
bcrypt = Bcrypt()
mail = Mail()
load_dotenv() # Load .env file into os.environ

# --- Helper Functions ---
def get_app_version(app_instance):
    try:
        project_root = os.path.abspath(os.path.join(app_instance.root_path, '..'))
        version_file_path = os.path.join(project_root, '.version')
        if not os.path.isfile(version_file_path):
             app_instance.logger.warning(f".version file not found at expected path: {version_file_path}. Defaulting to 'dev'.")
             return 'dev'
        with open(version_file_path, 'r') as f:
            version = f.read().strip()
            if not version:
                 app_instance.logger.warning(f".version file at {version_file_path} is empty. Defaulting to 'empty'.")
                 return 'empty'
            return version
    except Exception as e:
        if hasattr(app_instance, 'logger'):
             app_instance.logger.error(f"Error reading .version file: {e}", exc_info=True)
        else:
             print(f"ERROR: Error reading .version file: {e}")
        return 'unknown'

# --- Application Factory ---
def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=False)

    # --- Configuration Loading ---
    flask_env = os.environ.get('FLASK_ENV', os.environ.get('NODE_ENV', 'development'))
    is_production = (flask_env == 'production')
    is_testing = (flask_env == 'testing')
    app.config['TESTING'] = is_testing
    print(f"INFO: Loading {'Production' if is_production else ('Testing' if is_testing else 'Development')} Configuration")
    app.config['DEBUG'] = not is_production and not is_testing

    # --- Database Configuration ---
    database_url = os.environ.get('DATABASE_URL')
    if is_testing:
        test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_app.db')
        database_url = f"sqlite:///{test_db_path}"
        print(f"INFO: Using TESTING database: {database_url}")
    elif not database_url:
        if is_production:
             raise ValueError("FATAL: DATABASE_URL environment variable not set in production environment")
        print("WARNING: DATABASE_URL environment variable not set. Using local SQLite 'backend/app.db'.")
        backend_folder_path = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(backend_folder_path, 'app.db')
        database_url = f"sqlite:///{db_path}"
    elif database_url.startswith('postgres://'):
         database_url = database_url.replace('postgresql://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Secret Key Configuration ---
    if is_testing:
        app.config['SECRET_KEY'] = 'testing-secret-key'
    else:
        flask_secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-insecure-flask-key-replace-in-dotenv' if not is_production else None)
        if not flask_secret_key: raise ValueError("FATAL: FLASK_SECRET_KEY environment variable not set in production environment")
        if flask_secret_key == 'dev-insecure-flask-key-replace-in-dotenv': print("WARNING: Using default insecure FLASK_SECRET_KEY.")
        app.config['SECRET_KEY'] = flask_secret_key

    # --- Serializer Initialization ---
    try:
        app.password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='password-reset-salt')
        app.logger.info("URLSafeTimedSerializer initialized and stored on app.")
    except Exception as e:
        app.logger.error(f"FATAL: Failed to initialize URLSafeTimedSerializer: {e}", exc_info=True)
        raise

    # --- Frontend URL Configuration ---
    default_frontend_url = 'http://localhost:8080'
    app.config['FRONTEND_BASE_URL'] = os.environ.get('FRONTEND_BASE_URL', default_frontend_url)
    if not app.config['FRONTEND_BASE_URL']:
         if is_production:
             app.logger.error("FATAL: FRONTEND_BASE_URL environment variable is not set (required for password reset emails).")
         else:
             app.logger.warning(f"FRONTEND_BASE_URL not set, defaulting to '{default_frontend_url}' for development.")
             app.config['FRONTEND_BASE_URL'] = default_frontend_url
    else:
        app.logger.info(f"FRONTEND_BASE_URL configured: {app.config['FRONTEND_BASE_URL']}")

    # --- Mail Configuration ---
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

    # --- Session Configuration ---
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = db
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'sessions'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_KEY_PREFIX'] = 'session:'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7)))
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # --- Application Version Loading ---
    app_version = get_app_version(app)
    app.config['APP_VERSION'] = app_version
    app.logger.info(f"Application Version loaded: {app.config.get('APP_VERSION')}")

    # --- Middleware ---
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

    # --- Initialize Extensions with App ---
    db.init_app(app)
    migrate.init_app(app, db)
    server_session.init_app(app)
    bcrypt.init_app(app)
    print(f"DEBUG MAIL: Server={app.config.get('MAIL_SERVER')}, Port={app.config.get('MAIL_PORT')}")
    print(f"DEBUG MAIL: Use TLS={app.config.get('MAIL_USE_TLS')}, Use SSL={app.config.get('MAIL_USE_SSL')}")
    print(f"DEBUG MAIL: Username={app.config.get('MAIL_USERNAME')}")
    mail.init_app(app)

    # --- Limiter Initialization ---
    if app.config.get("TESTING"):
        limiter.init_app(app)
        limiter.enabled = False
        app.logger.info("Rate limiting DISABLED for TESTING environment.")
    else:
        limiter.enabled = True
        redis_url = os.environ.get('REDIS_URL')
        if is_production and not redis_url:
            app.logger.warning("REDIS_URL environment variable not set in Production. Rate limiting will use memory storage (may be inconsistent).")
            limiter_storage_uri = "memory://"
        elif redis_url:
            limiter_storage_uri = redis_url
            app.logger.info("Rate limiting ENABLED using Redis.")
        else:
            limiter_storage_uri = "memory://"
            app.logger.info("Rate limiting ENABLED using in-memory storage (development).")
        app.config['RATELIMIT_STORAGE_URL'] = limiter_storage_uri
        limiter.init_app(app)

    # --- Error Handlers ---
    @app.errorhandler(429)
    def ratelimit_handler(e):
        message = str(e.description) if hasattr(e, 'description') and e.description else "Rate limit exceeded"
        return jsonify(error="ratelimit exceeded", message=message), 429

    # --- Template Context Processors ---
    @app.context_processor
    def inject_global_context():
        return dict(
            app_version=app.config.get('APP_VERSION', 'unknown'),
            current_year=date.today().year
        )

    # --- Request Hooks ---
    @app.before_request
    def generate_csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(16)

    # --- Blueprint Registration ---
    try:
        from backend.routes import register_routes
        register_routes(app)
        print("INFO: Routes registered successfully.")
    except ImportError as e:
        print(f"ERROR: Could not import or register routes: {e}")
        if app.config.get("TESTING"):
            raise RuntimeError(f"Failed to register routes during testing: {e}") from e
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during route registration: {e}")
        if app.config.get("TESTING"):
            raise RuntimeError(f"Unexpected error during route registration: {e}") from e

    # --- CLI Commands ---
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
        with app.app_context():
            try:
                print(f"INFO: Ensure the '{app.config['SESSION_SQLALCHEMY_TABLE']}' table exists via 'flask db upgrade'.")
            except Exception as e:
                app.logger.error(f"Error during session table check/creation command: {e}")
        return app

    return app