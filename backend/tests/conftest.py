import pytest
import os
from backend import create_app, db as _db
from flask_bcrypt import Bcrypt
from flask.testing import FlaskClient
from backend.models import User, Commander, DeckType, Deck, CommanderDeck, Tag, UserDeck, Match
from sqlalchemy import select, delete
from datetime import datetime, timezone
import logging # Import logging

# Store original env vars to restore later
ORIGINAL_DATABASE_URL = os.environ.get('DATABASE_URL')
ORIGINAL_FLASK_ENV = os.environ.get('FLASK_ENV')

@pytest.fixture(scope='session')
def app():
    """Creates and configures a Flask app instance FOR TESTING."""

    # Force a testing environment and in-memory database via environment variables
    test_db_uri = 'sqlite:///:memory:'
    print(f"INFO [conftest]: Setting DATABASE_URL for test session: {test_db_uri}")
    os.environ['DATABASE_URL'] = test_db_uri
    os.environ['FLASK_ENV'] = 'testing'

    # Create the app - it will read the environment variables
    app = create_app()
    print(f"INFO [conftest]: App DB URI after create_app: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

    # --- START MODIFICATION ---
    # Manually ensure TESTING config is True, as create_app doesn't set it from FLASK_ENV
    print(f"INFO [conftest]: Forcing app.config['TESTING'] = True")
    app.config['TESTING'] = True
    # Remove the assertion that was failing, as we now set it manually:
    # assert app.config['TESTING'] is True # REMOVE OR COMMENT OUT THIS LINE

    # Ensure other necessary test configs are set
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    # --- END MODIFICATION ---

    with app.app_context():
        print("INFO [conftest]: Dropping and Creating all tables in test database...")
        _db.drop_all()
        _db.create_all()
        print("INFO [conftest]: Tables created in test database.")

        # Attempt to create Flask-Session table if needed
        try:
            from flask import current_app
            if hasattr(current_app, 'session_interface') and \
               hasattr(current_app.session_interface, 'db') and \
               current_app.session_interface.db:
                current_app.session_interface.db.create_all()
                print("INFO [conftest]: Flask-Session table creation attempted.")
        except Exception as e:
            print(f"WARN [conftest]: Could not attempt Flask-Session table creation: {e}")

        yield app

        # Teardown: Restore original environment variables
        print("INFO [conftest]: Test session finished. Restoring environment.")
        if ORIGINAL_DATABASE_URL is None:
            if 'DATABASE_URL' in os.environ: del os.environ['DATABASE_URL']
        else:
            os.environ['DATABASE_URL'] = ORIGINAL_DATABASE_URL

        if ORIGINAL_FLASK_ENV is None:
            if 'FLASK_ENV' in os.environ: del os.environ['FLASK_ENV']
        else:
            os.environ['FLASK_ENV'] = ORIGINAL_FLASK_ENV


# --- Keep the rest of the fixtures (client, db, test_user, logged_in_client, commanders, setup_deck) ---
# --- as they were in the previous correct version ---

@pytest.fixture(scope='session')
def client(app) -> FlaskClient:
    """Provides a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Provides a database session fixture with rollback for test isolation."""
    with app.app_context():
        yield _db
        _db.session.rollback()
        _db.session.remove()


@pytest.fixture(scope='function')
def test_user(app, db): # Depend on the function-scoped db fixture
    """Creates a test user for authentication tests."""
    bcrypt = Bcrypt(app)
    username = "testuser_session" # Consistent username for tests
    password = "password123"
    user = None # Initialize user variable
    logger = logging.getLogger("conftest") # Get logger instance

    with app.app_context():
        existing_user = db.session.scalar(select(User).where(User.username == username))
        if existing_user:
            logger.warning(f"Found existing user '{username}' in function-scoped fixture setup. Attempting cleanup.")
            try:
                # Example cleanup (adjust based on your foreign keys)
                # db.session.execute(delete(Deck).where(Deck.user_id == existing_user.id))
                # db.session.execute(delete(Tag).where(Tag.user_id == existing_user.id))
                # ... etc for other dependencies ...
                db.session.delete(existing_user)
                db.session.commit()
            except Exception as e:
                logger.error(f"Error cleaning up existing user '{username}' in fixture: {e}")
                db.session.rollback() # Rollback the failed cleanup attempt
                pytest.fail(f"Failed to clean up existing user '{username}' before test.")


        # Create the test user for this function's scope
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit() # Commit the user so it's available for login
        db.session.refresh(user) # Get the user ID
        print(f"INFO [conftest]: Created user {user.id} ({user.username}) for test.")

        yield {"user_obj": user, "password": password}

        # Teardown handled by 'db' fixture rollback/remove
        print(f"INFO [conftest]: Tearing down test_user fixture for user {user.id if user else 'N/A'}.")


@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    """Provides a test client that is logged in as the test_user."""
    login_resp = client.post('/api/auth/login', json={
        'username': test_user["user_obj"].username,
        'password': test_user["password"]
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.get_data(as_text=True)}"

    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200, f"CSRF fetch failed: {csrf_resp.get_data(as_text=True)}"
    csrf_token_data = csrf_resp.get_json()
    assert csrf_token_data is not None, "CSRF response was not valid JSON"
    assert 'csrf_token' in csrf_token_data, "CSRF token missing from response"
    csrf_token = csrf_token_data['csrf_token']

    # Add some debugging prints
    print(f"DEBUG LOGIN [conftest]: Session established for user {test_user['user_obj'].id}, username {test_user['user_obj'].username}")
    print(f"DEBUG LOGIN [conftest]: Session CSRF Token: {csrf_token}")
    session_cookie = client.get_cookie('session')
    if session_cookie:
        print(f"DEBUG LOGIN [conftest]: Session ID (in cookie): {session_cookie.value}")
    else:
        print("DEBUG LOGIN [conftest]: Session cookie not found.")

    yield client, csrf_token


@pytest.fixture(scope='function')
def commanders(app, db):
     """Creates necessary commander objects for testing."""
     with app.app_context():
        deck_type_id = 7
        deck_type_name = 'Commander / EDH'
        dt = db.session.get(DeckType, deck_type_id)
        if not dt:
            dt = db.session.scalar(select(DeckType).where(DeckType.name == deck_type_name))
            if not dt:
                dt = DeckType(id=deck_type_id, name=deck_type_name)
                db.session.add(dt)

        cmdrs_data = {
            "no_partner": {"name": "Solo Cmdr Sesh", "scryfall_id": "solo1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "can_partner_1": {"name": "Partner Cmdr 1 Sesh", "scryfall_id": "p1_s", "partner": True, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "can_partner_2": {"name": "Partner Cmdr 2 Sesh", "scryfall_id": "p2_s", "partner": True, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "ff_1": {"name": "FF Cmdr 1 Sesh", "scryfall_id": "ff1_s", "partner": False, "friends_forever": True, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "ff_2": {"name": "FF Cmdr 2 Sesh", "scryfall_id": "ff2_s", "partner": False, "friends_forever": True, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "doctor": {"name": "The Doctor Sesh", "scryfall_id": "doc1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": True, "doctor_companion": False, "background": False},
            "companion": {"name": "The Companion Sesh", "scryfall_id": "comp1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": True, "background": False},
            "needs_bg": {"name": "Needs Background Sesh", "scryfall_id": "nbg1_s", "partner": False, "friends_forever": False, "choose_a_background": True, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "is_bg": {"name": "Is Background Sesh", "scryfall_id": "bg1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": True},
            "invalid_partner": {"name": "Not Partner Sesh", "scryfall_id": "invp1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_ff": {"name": "Not FF Sesh", "scryfall_id": "invff1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_bg": {"name": "Not BG Sesh", "scryfall_id": "invbg1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_doctor": {"name": "Not Doctor Sesh", "scryfall_id": "invdoc1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_companion": {"name": "Not Companion Sesh", "scryfall_id": "invcomp1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False}
        }
        cmdrs = {}
        needs_commit = False
        for key, data in cmdrs_data.items():
            cmdr = db.session.scalar(select(Commander).where(Commander.scryfall_id == data['scryfall_id']))
            if not cmdr:
                cmdr = Commander(**data)
                db.session.add(cmdr)
                needs_commit = True
            cmdrs[key] = cmdr

        if needs_commit:
            db.session.commit()

        commander_ids = {}
        for key, cmdr_obj in cmdrs.items():
             if cmdr_obj.id is None: db.session.refresh(cmdr_obj)
             if cmdr_obj.id is None: raise Exception(f"Commander '{key}' failed to get an ID.")
             commander_ids[key] = cmdr_obj.id

        yield commander_ids


@pytest.fixture(scope='function')
def setup_deck(db, test_user, commanders):
    """Sets up a basic deck, user_deck, tag, and match for tests."""
    logger = logging.getLogger("conftest") # Get logger instance
    with db.app.app_context():
        user = test_user['user_obj']
        if user is None or user.id is None:
             pytest.fail("test_user fixture failed to provide a valid user object.")

        commander_no_partner_id = commanders.get('no_partner')
        if commander_no_partner_id is None:
             pytest.fail("Could not find 'no_partner' commander ID in commanders fixture.")
        commander_no_partner = db.session.get(Commander, commander_no_partner_id)
        if not commander_no_partner:
             pytest.fail(f"Commander with ID {commander_no_partner_id} ('no_partner') not found in DB.")

        deck = Deck(name="Base Test Deck", deck_type_id=7, user_id=user.id)
        db.session.add(deck)
        db.session.flush()

        user_deck = UserDeck(user_id=user.id, deck_id=deck.id)
        db.session.add(user_deck)
        db.session.flush()

        commander_deck = CommanderDeck(deck_id=deck.id, commander_id=commander_no_partner_id)
        db.session.add(commander_deck)

        tag = Tag(name="Base Tag", user_id=user.id)
        db.session.add(tag) # Add tag first
        db.session.flush() # Get tag ID
        deck.tags.append(tag) # Associate tag with deck

        match = Match(timestamp=datetime.now(timezone.utc), result=1, user_deck_id=user_deck.id)
        db.session.add(match)
        db.session.flush() # Get match ID
        match.tags.append(tag) # Associate tag with match

        try:
            db.session.commit()
            print(f"INFO [conftest]: Committed setup_deck data (Deck ID: {deck.id}, UserDeck ID: {user_deck.id}, Tag ID: {tag.id}, Match ID: {match.id})")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing setup_deck data: {e}", exc_info=True)
            pytest.fail(f"Failed to commit setup_deck data: {e}")

        yield {'deck': deck, 'tag': tag, 'match': match, 'user_deck': user_deck}
        # Teardown handled by db fixture rollback