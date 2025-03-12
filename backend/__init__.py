from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)

    # Configuración de la base de datos
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar SQLAlchemy
    db.init_app(app)

    # Importar y registrar Blueprints (rutas)
    from .routes.auth import auth_bp
    from .routes.frontend import frontend_bp
    from .routes.matches import matches_bp
    from .routes.decks import decks_bp
    from .routes.deck_types import deck_types_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(decks_bp)
    app.register_blueprint(deck_types_bp, url_prefix='/api')

    return app
