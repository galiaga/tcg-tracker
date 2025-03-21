import pytest
from backend import create_app, db
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask.testing import FlaskClient

bcrypt = Bcrypt()
jwt = JWTManager()

@pytest.fixture
def app():
    app = create_app("testing")
    bcrypt.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()
