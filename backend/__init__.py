from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

import os

db = SQLAlchemy(session_options={"autocommit": False, "autoflush": False})
jwt = JWTManager()

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
        app.config["JWT_SECRET_KEY"] = "testing-secret"
        app.config["JWT_TOKEN_LOCATION"] = ["headers"]

    db.init_app(app)

    jwt.init_app(app)

    from backend.routes import register_routes
    register_routes(app)

    Migrate(app, db)
    
    return app
