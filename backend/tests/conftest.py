import pytest
from backend import create_app, db as _db
from flask_bcrypt import Bcrypt
from flask.testing import FlaskClient
from backend.models import User

# bcrypt = Bcrypt() # Only needed if you use bcrypt directly in fixtures

@pytest.fixture(scope='session')
def app():
    """Creates and configures a Flask app instance for testing."""
    # Assuming create_app uses FLASK_ENV=testing now from the workflow
    app = create_app()
    # bcrypt.init_app(app) # Initialize if needed by the app itself

    with app.app_context():
        # Drop and recreate tables ONCE per session
        _db.drop_all()
        _db.create_all()

        # Attempt to create Flask-Session table if needed (keep this)
        try:
            from flask import current_app
            if hasattr(current_app, 'session_interface') and \
               hasattr(current_app.session_interface, 'db') and \
               current_app.session_interface.db:
                # Use the correct db object associated with Flask-Session
                current_app.session_interface.db.create_all()
                print("INFO: Flask-Session table creation attempted.")
        except Exception as e:
            print(f"WARN: Could not attempt Flask-Session table creation: {e}")

        yield app

        # Optional: Clean up session-level stuff if necessary,
        # but the drop_all here might be redundant if the runner destroys the container
        # _db.session.remove()
        # _db.drop_all() # Maybe remove this final drop_all if relying on container teardown


@pytest.fixture(scope='session')
def client(app) -> FlaskClient:
    """Provides a test client for the Flask application."""
    return app.test_client()


# --- MODIFIED FIXTURE ---
@pytest.fixture(scope='function')
def db(app):
    """Provides a database session fixture with rollback for test isolation."""
    with app.app_context():
        # --- REMOVED this pre-test deletion ---
        # _db.session.query(User).delete()
        # _db.session.commit()
        # --- END REMOVAL ---

        # Start a transaction implicitly (SQLAlchemy usually does this)
        # or explicitly: _db.session.begin_nested() # Or just rely on rollback

        yield _db # Test runs here, potentially adding data

        # Rollback any changes made during the test
        # This effectively cleans up data added *within* the test function
        _db.session.rollback()
        _db.session.remove() # Detach all objects from the session