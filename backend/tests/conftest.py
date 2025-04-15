import pytest
from backend import create_app, db as _db
from flask_bcrypt import Bcrypt
from flask.testing import FlaskClient
from backend.models import User

bcrypt = Bcrypt()

@pytest.fixture(scope='session')
def app():
    """Creates and configures a Flask app instance for testing."""
    app = create_app("testing")
    bcrypt.init_app(app)

    with app.app_context():
        _db.drop_all()
        _db.create_all()

        try:
            from flask import current_app
            if hasattr(current_app, 'session_interface') and \
               hasattr(current_app.session_interface, 'db') and \
               current_app.session_interface.db:
                current_app.session_interface.db.create_all(bind_key=None)
                print("INFO: Flask-Session table creation attempted.")
        except Exception as e:
            print(f"WARN: Could not attempt Flask-Session table creation: {e}")

        yield app 

        _db.drop_all()

@pytest.fixture(scope='session')
def client(app) -> FlaskClient:
    """Provides a test client for the Flask application."""
    return app.test_client()

@pytest.fixture(scope='function')
def db(app):
    """Provides a database session fixture with rollback."""
    with app.app_context():
        _db.session.query(User).delete()
        _db.session.commit() 

        yield _db

        _db.session.rollback()
        _db.session.remove()
