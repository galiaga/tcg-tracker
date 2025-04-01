import pytest
from backend import create_app, db as _db
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
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()

@pytest.fixture(scope="function")
def db(app):
    yield _db
    _db.session.rollback()
    _db.drop_all()
    _db.create_all()
