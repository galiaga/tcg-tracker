# backend/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate # Asegúrate que Migrate esté disponible para app.py si se inicializa allí
from flask_jwt_extended import JWTManager
from datetime import timedelta

# --- Extension Objects ---
# Definidos globalmente para ser importados en otros módulos (como models.py o app.py)
db = SQLAlchemy(session_options={"autocommit": False, "autoflush": False})
jwt = JWTManager()
# Considera definir migrate aquí también si usas init_app en la factory:
# migrate = Migrate()

# --- Application Factory ---
def create_app(config_name=None):
    """Flask application factory."""
    app = Flask(__name__, instance_relative_config=False) # instance_relative_config=False es común si no usas la carpeta instance activamente para config

    # Determina el entorno (por defecto 'development' si no se establece)
    # Lee FLASK_ENV o NODE_ENV (Fly.io puede setear NODE_ENV)
    flask_env = os.environ.get('FLASK_ENV', os.environ.get('NODE_ENV', 'development'))
    is_production = (flask_env == 'production')

    # Carga configuración base o específica del entorno si tuvieras archivos separados
    # app.config.from_object('config.DefaultConfig') # Ejemplo si tuvieras clases de config
    # if is_production:
    #     app.config.from_object('config.ProductionConfig')
    # else:
    #     app.config.from_object('config.DevelopmentConfig')

    print(f"INFO: Loading {'Production' if is_production else 'Development'} Configuration")
    app.config['DEBUG'] = not is_production # Debug=True en dev, False en prod

    # --- Configuración de Base de Datos ---
    database_url = os.environ.get('DATABASE_URL') # Lee la variable de entorno

    if not database_url:
        # Fallback a SQLite local SOLO si no es producción y DATABASE_URL no está definida
        if is_production:
             # Fallar rápido si no hay BD configurada en producción
             raise ValueError("FATAL: DATABASE_URL environment variable not set in production environment")

        print("WARNING: DATABASE_URL environment variable not set. Using local SQLite 'backend/app.db'.")
        # Construir ruta absoluta a backend/app.db
        backend_folder_path = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(backend_folder_path, 'app.db')
        database_url = f"sqlite:///{db_path}"

    elif database_url.startswith('postgres://'):
         # Asegurar compatibilidad URI para SQLAlchemy si Fly.io da postgres://
         database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"--- DEBUG: Connecting to DB: {app.config['SQLALCHEMY_DATABASE_URI']} ---") # Para verificar
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Práctica recomendada

    # --- Configuración de Secret Keys ---
    flask_secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not flask_secret_key:
        if is_production:
            raise ValueError("FATAL: FLASK_SECRET_KEY environment variable not set in production environment")
        else:
            print("WARNING: FLASK_SECRET_KEY not set. Using default insecure key for development.")
            flask_secret_key = 'dev-insecure-flask-key-replace-in-dotenv' # Clave insegura SÓLO para dev
    app.config['SECRET_KEY'] = flask_secret_key # Flask usa SECRET_KEY

    jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret_key:
        if is_production:
            raise ValueError("FATAL: JWT_SECRET_KEY environment variable not set in production environment")
        else:
            print("WARNING: JWT_SECRET_KEY not set. Using default insecure key for development.")
            jwt_secret_key = 'dev-insecure-jwt-key-replace-in-dotenv' # Clave insegura SÓLO para dev
    app.config['JWT_SECRET_KEY'] = jwt_secret_key

    # --- Configuración JWT Adicional ---
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    # Podrías cargar estos tiempos desde env vars si necesitas más flexibilidad
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=int(os.environ.get('JWT_ACCESS_MINUTES', 15)))
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=int(os.environ.get('JWT_REFRESH_DAYS', 7)))

    # --- Inicializar Extensiones ---
    db.init_app(app)
    jwt.init_app(app)
    # Si definiste migrate globalmente:
    # migrate.init_app(app, db)
    # Si inicializas otras extensiones como Bcrypt aquí:
    # bcrypt = Bcrypt() # Necesitarías importar Bcrypt
    # bcrypt.init_app(app)

    # --- Registrar Rutas/Blueprints ---
    try:
        from backend.routes import register_routes
        register_routes(app)
        print("INFO: Routes registered successfully.")
    except ImportError as e:
        print(f"ERROR: Could not import or register routes: {e}")
        # Considera si debes lanzar un error aquí o manejarlo de otra forma

    # Nota: La inicialización de Migrate y Bcrypt que tenías en app.py
    # (después de llamar a create_app) también es un patrón válido.
    # Asegúrate de que solo se inicialicen una vez.

    # --- Retornar la App Configurada ---
    return app