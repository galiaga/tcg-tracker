from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy(session_options={"autocommit": False, "autoflush": False})

def create_app(config_name=None):
    app = Flask(__name__)

    if config_name == "testing":
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            WTF_CSRF_ENABLED=False,
            JWT_SECRET_KEY="testing-secret"
        )
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    import backend.models
    
    from backend.models import user, deck, user_deck, match, commanders
    
    from .routes.auth import auth_bp
    from .routes.frontend import frontend_bp
    from .routes.matches import matches_bp
    from .routes.deck_types import deck_types_bp
    from .routes.commanders import commanders_bp
    from .routes.match_history import matches_history_bp 
    from .routes.decks.user_decks import user_decks_bp 
    from backend.routes import register_routes

    app.register_blueprint(auth_bp)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(deck_types_bp, url_prefix='/api')
    app.register_blueprint(commanders_bp, url_prefix='/api')
    app.register_blueprint(matches_history_bp, url_prefix='/api')
    app.register_blueprint(user_decks_bp, url_prefix='/api')

    register_routes(app)

    Migrate(app, db)
    
    return app
