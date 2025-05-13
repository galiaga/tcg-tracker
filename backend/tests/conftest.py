# backend/tests/conftest.py

import pytest
import os
from backend import create_app, db as _db
from flask_bcrypt import Bcrypt
from flask.testing import FlaskClient
# Updated import: Replace Match with LoggedMatch
from backend.models import (
    User, Commander, DeckType, Deck, CommanderDeck, Tag, UserDeck, LoggedMatch,
    Tournament, TournamentParticipant # Also import new models if tests will use them
)
from sqlalchemy import select, delete
from datetime import datetime, timezone
import logging

ORIGINAL_DATABASE_URL = os.environ.get('DATABASE_URL')
ORIGINAL_FLASK_ENV = os.environ.get('FLASK_ENV')
logger = logging.getLogger("conftest")

@pytest.fixture(scope='session')
def app():
    """Creates and configures a Flask app instance FOR TESTING."""
    test_db_uri = 'sqlite:///:memory:' # Use in-memory for speed and isolation
    logger.info(f"Setting DATABASE_URL for test session: {test_db_uri}")
    os.environ['DATABASE_URL'] = test_db_uri
    os.environ['FLASK_ENV'] = 'testing'

    app_instance = create_app() # Get the app instance

    # Configure specifically for testing AFTER app creation
    app_instance.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
        RATELIMIT_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=test_db_uri, # Ensure test URI is used
        SQLALCHEMY_ECHO=True  # <--- SET IT HERE on the created app instance
    )
    logger.info(f"App DB URI after create_app and config update: {app_instance.config.get('SQLALCHEMY_DATABASE_URI')}")
    logger.info(f"SQLALCHEMY_ECHO set to: {app_instance.config.get('SQLALCHEMY_ECHO')}")


    with app_instance.app_context():
        logger.info("Dropping and Creating all tables in test database...")
        _db.drop_all() # _db here is from backend.database, initialized with app_instance
        _db.create_all()
        logger.info("Tables created in test database.")

        # Flask-Session table creation (if needed)
        try:
            if hasattr(app_instance, 'session_interface') and \
               hasattr(app_instance.session_interface, 'db') and \
               app_instance.session_interface.db: # Check if Flask-Session uses SQLAlchemy
                # This assumes Flask-Session is configured to use the same _db instance
                # If it creates its own tables, this might not be needed or might need adjustment
                # For now, let's assume _db.create_all() covers it if configured with same metadata
                pass # _db.create_all() should handle the 'sessions' table if it's part of _db.metadata
                logger.info("Flask-Session table should be covered by _db.create_all().")
        except Exception as e:
            logger.warning(f"Note on Flask-Session table creation: {e}")

        yield app_instance # Yield the configured app instance

        logger.info("Test session finished. Restoring environment.")
        if ORIGINAL_DATABASE_URL is None:
            if 'DATABASE_URL' in os.environ: del os.environ['DATABASE_URL']
        else:
            os.environ['DATABASE_URL'] = ORIGINAL_DATABASE_URL

        if ORIGINAL_FLASK_ENV is None:
            if 'FLASK_ENV' in os.environ: del os.environ['FLASK_ENV']
        else:
            os.environ['FLASK_ENV'] = ORIGINAL_FLASK_ENV

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
        # Remove session to ensure clean state, rollback handles most cases
        _db.session.remove()

@pytest.fixture(scope='function')
def test_user(app, db):
    """Creates a test user for authentication tests."""
    bcrypt = Bcrypt(app)
    username = "testuser_conftest" # Use a distinct name
    password = "password123"
    email = "test_conftest@example.com"
    first_name = "Test"
    last_name = "User"
    user = None

    with app.app_context():
        # Clean up potentially existing user from previous failed test runs
        existing_user = db.session.scalar(select(User).where(User.username == username))
        if existing_user:
            logger.warning(f"Found existing user '{username}' in fixture setup. Cleaning up.")
            # Add more cleanup as needed based on FKs
            db.session.execute(delete(LoggedMatch).where(LoggedMatch.logger_user_id == existing_user.id))
            db.session.execute(delete(Deck).where(Deck.user_id == existing_user.id)) # Cascades should handle CommanderDeck, UserDeck
            db.session.execute(delete(Tag).where(Tag.user_id == existing_user.id))
            db.session.execute(delete(Tournament).where(Tournament.organizer_id == existing_user.id)) # Cascades handle participants
            # Add other direct user dependencies if necessary
            db.session.delete(existing_user)
            try:
                db.session.commit()
            except Exception as e_cleanup:
                logger.error(f"Error during test_user cleanup commit: {e_cleanup}")
                db.session.rollback()
                pytest.fail(f"Failed to clean up existing user '{username}' before test.")

        # Create the test user
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            username=username,
            password_hash=hashed_password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(user)
        try:
            db.session.commit()
            db.session.refresh(user) # Get the user ID
            logger.info(f"Created user {user.id} ({user.username}) for test.")
        except Exception as e_create:
            logger.error(f"Error committing new test user: {e_create}")
            db.session.rollback()
            pytest.fail(f"Failed to create test user '{username}'.")

        yield {"user_obj": user, "password": password}

        # Teardown handled by 'db' fixture rollback/remove
        logger.info(f"Tearing down test_user fixture for user {user.id if user else 'N/A'}.")

@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    """Provides a test client that is logged in as the test_user."""
    login_resp = client.post('/api/auth/login', json={
        'email': test_user["user_obj"].email,
        'password': test_user["password"]
    })
    if login_resp.status_code != 200:
         pytest.fail(f"Login failed in fixture: {login_resp.status_code} {login_resp.get_data(as_text=True)}")

    csrf_resp = client.get('/api/auth/csrf_token')
    if csrf_resp.status_code != 200:
         pytest.fail(f"CSRF fetch failed in fixture: {csrf_resp.status_code} {csrf_resp.get_data(as_text=True)}")
    csrf_token_data = csrf_resp.get_json()
    if not csrf_token_data or 'csrf_token' not in csrf_token_data:
         pytest.fail("CSRF token missing or invalid response in fixture")
    csrf_token = csrf_token_data['csrf_token']

    logger.debug(f"Logged in client fixture setup complete for user {test_user['user_obj'].id}")
    yield client, csrf_token # Yield client and token together
    logger.debug(f"Logged in client fixture teardown for user {test_user['user_obj'].id}")
    # Logout is not strictly necessary due to function scope and client isolation

@pytest.fixture(scope='function')
def test_user_2(app, db):
    """Creates a secondary test user."""
    bcrypt = Bcrypt(app)
    username = "testuser2_conftest" # Unique username
    password = "password456"
    email = "test_conftest_2@example.com" # Unique email
    first_name = "Test"
    last_name = "UserTwo"
    user = None

    with app.app_context():
        # Cleanup logic similar to test_user
        existing_user = db.session.scalar(select(User).where(User.email == email))
        if existing_user:
            logger.warning(f"Found existing user '{email}' (user 2) in fixture setup. Cleaning up.")
            # Add cleanup for user 2's potential data
            db.session.execute(delete(LoggedMatch).where(LoggedMatch.logger_user_id == existing_user.id))
            db.session.execute(delete(Deck).where(Deck.user_id == existing_user.id))
            db.session.execute(delete(Tag).where(Tag.user_id == existing_user.id))
            db.session.execute(delete(Tournament).where(Tournament.organizer_id == existing_user.id))
            db.session.delete(existing_user)
            try:
                db.session.commit()
            except Exception as e_cleanup:
                logger.error(f"Error during test_user_2 cleanup commit: {e_cleanup}")
                db.session.rollback()
                pytest.fail(f"Failed to clean up existing user '{email}' (user 2) before test.")

        # Create user 2
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            username=username,
            password_hash=hashed_password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(user)
        try:
            db.session.commit()
            db.session.refresh(user)
            logger.info(f"Created user {user.id} ({user.username}) for test (user 2).")
        except Exception as e_create:
            logger.error(f"Error committing new test user 2: {e_create}")
            db.session.rollback()
            pytest.fail(f"Failed to create test user '{username}' (user 2).")

        yield {"user_obj": user, "password": password}

        logger.info(f"Tearing down test_user_2 fixture for user {user.id if user else 'N/A'}.")


@pytest.fixture(scope='function')
def logged_in_client_user_2(client, test_user_2):
    """Provides a test client that is logged in as test_user_2."""
    login_resp = client.post('/api/auth/login', json={
        'email': test_user_2["user_obj"].email, # Use email key
        'password': test_user_2["password"]
    })
    if login_resp.status_code != 200:
         pytest.fail(f"Login failed in fixture (user 2): {login_resp.status_code} {login_resp.get_data(as_text=True)}")

    csrf_resp = client.get('/api/auth/csrf_token')
    if csrf_resp.status_code != 200:
         pytest.fail(f"CSRF fetch failed in fixture (user 2): {csrf_resp.status_code} {csrf_resp.get_data(as_text=True)}")
    csrf_token_data = csrf_resp.get_json()
    if not csrf_token_data or 'csrf_token' not in csrf_token_data:
         pytest.fail("CSRF token missing or invalid response in fixture (user 2)")
    csrf_token = csrf_token_data['csrf_token']

    logger.debug(f"Logged in client fixture setup complete for user {test_user_2['user_obj'].id}")
    yield client, csrf_token
    logger.debug(f"Logged in client fixture teardown for user {test_user_2['user_obj'].id}")

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

        # Simplified data for brevity in example
        cmdrs_data = {
            "no_partner": {"name": "Solo Cmdr Test", "scryfall_id": "solo1_test", "partner": False, "choose_a_background": False},
            "can_partner_1": {"name": "Partner Cmdr 1 Test", "scryfall_id": "p1_test", "partner": True},
            "can_partner_2": {"name": "Partner Cmdr 2 Test", "scryfall_id": "p2_test", "partner": True},
            "needs_bg": {"name": "Needs Background Test", "scryfall_id": "nbg1_test", "choose_a_background": True},
            "is_bg": {"name": "Is Background Test", "scryfall_id": "bg1_test", "background": True},
        }
        cmdrs = {}
        needs_commit = False
        for key, data in cmdrs_data.items():
            # Ensure all boolean flags are present, defaulting to False
            full_data = {
                "name": data["name"], "scryfall_id": data["scryfall_id"],
                "partner": data.get("partner", False), "friends_forever": data.get("friends_forever", False),
                "choose_a_background": data.get("choose_a_background", False),
                "time_lord_doctor": data.get("time_lord_doctor", False),
                "doctor_companion": data.get("doctor_companion", False),
                "background": data.get("background", False)
            }
            cmdr = db.session.scalar(select(Commander).where(Commander.scryfall_id == full_data['scryfall_id']))
            if not cmdr:
                cmdr = Commander(**full_data)
                db.session.add(cmdr)
                needs_commit = True
            cmdrs[key] = cmdr

        if needs_commit:
            db.session.commit()

        commander_ids = {}
        for key, cmdr_obj in cmdrs.items():
             if cmdr_obj.id is None: db.session.refresh(cmdr_obj) # Ensure ID is loaded
             if cmdr_obj.id is None: raise Exception(f"Commander '{key}' failed to get an ID after commit/refresh.")
             commander_ids[key] = cmdr_obj.id

        yield commander_ids # Yield IDs for tests to use

@pytest.fixture(scope='function')
def setup_deck(db, test_user, commanders):
    """Sets up a basic deck, tag, and logged_match for tests."""
    with db.app.app_context():
        user = test_user['user_obj']
        if not user or not user.id:
             pytest.fail("setup_deck: test_user fixture failed.")

        commander_id = commanders.get('no_partner')
        if not commander_id:
             pytest.fail("setup_deck: Could not find 'no_partner' commander ID.")

        # Create Deck
        deck = Deck(name="Base Test Deck", deck_type_id=7, user_id=user.id)
        db.session.add(deck)
        db.session.flush() # Get deck ID

        # Create CommanderDeck link
        commander_deck = CommanderDeck(deck_id=deck.id, commander_id=commander_id)
        db.session.add(commander_deck)

        # Create Tag
        tag = Tag(name="Base Tag", user_id=user.id)
        db.session.add(tag)
        db.session.flush() # Get tag ID

        # Associate Tag with Deck
        deck.tags.append(tag)

        # --- Create LoggedMatch (Updated) ---
        logged_match = LoggedMatch(
            timestamp=datetime.now(timezone.utc),
            result=1, # Example: Win
            logger_user_id=user.id, # Use direct user ID
            deck_id=deck.id # Use direct deck ID
        )
        db.session.add(logged_match)
        db.session.flush() # Get logged_match ID

        # Associate Tag with LoggedMatch
        logged_match.tags.append(tag)
        # --- End LoggedMatch Creation ---

        # Create UserDeck (keep for potential compatibility if other tests use it)
        user_deck = UserDeck(user_id=user.id, deck_id=deck.id)
        db.session.add(user_deck)

        try:
            db.session.commit()
            logger.info(f"Committed setup_deck data (Deck ID: {deck.id}, Tag ID: {tag.id}, LoggedMatch ID: {logged_match.id})")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing setup_deck data: {e}", exc_info=True)
            pytest.fail(f"Failed to commit setup_deck data: {e}")

        # Yield the relevant objects, including the new logged_match
        yield {'deck': deck, 'tag': tag, 'logged_match': logged_match, 'user_deck': user_deck}
        # Teardown handled by db fixture rollback