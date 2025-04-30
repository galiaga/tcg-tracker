# backend/tests/auth/test_profile_update.py

# --- Imports ---
import pytest
import secrets
from flask_bcrypt import Bcrypt
from sqlalchemy import select
from backend import db as _db # Use alias to avoid conflict with pytest 'db' fixture
from backend.models import User

# --- Fixtures ---

bcrypt = Bcrypt() # Initialize globally for fixtures

@pytest.fixture(scope='function')
def test_user(app, db):
    """Creates or retrieves the primary test user for profile updates."""
    email = "profileupdate@example.com"
    first_name = "Update"
    last_name = "Me"
    username = f"update_user_{secrets.token_hex(4)}" # Start with a username
    password = "password123"
    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user: user = _db.session.scalar(select(User).where(User.username == username))

        if not user:
            print(f"\nDEBUG: Creating user for profile update tests: {email}")
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email.lower(),
                username=username,
                password_hash=hashed_password
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        else:
            print(f"\nDEBUG: Found existing user for profile update tests: {user.email}")
            needs_update = False
            # Ensure fields are set to expected initial state for tests
            if user.first_name != first_name: user.first_name = first_name; needs_update = True
            if user.last_name != last_name: user.last_name = last_name; needs_update = True
            if user.email != email.lower(): user.email = email.lower(); needs_update = True
            if user.username != username: user.username = username; needs_update = True
            if not bcrypt.check_password_hash(user.password_hash, password):
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 needs_update = True
            if needs_update:
                 _db.session.commit()
                 _db.session.refresh(user)

        yield {"user_obj": user, "password": password}

@pytest.fixture(scope='function')
def test_user_2(app, db):
    """Creates or retrieves a secondary test user for conflict tests."""
    email = "profileconflict@example.com"
    first_name = "Conflict"
    last_name = "User"
    username = f"conflict_user_{secrets.token_hex(4)}" # Ensure this user has a username
    password = "password456"
    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user: user = _db.session.scalar(select(User).where(User.username == username))

        if not user:
            print(f"\nDEBUG: Creating user 2 for profile conflict tests: {email}")
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email.lower(),
                username=username,
                password_hash=hashed_password
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        else:
            print(f"\nDEBUG: Found existing user 2 for profile conflict tests: {user.email}")
            needs_update = False
            if user.first_name != first_name: user.first_name = first_name; needs_update = True
            if user.last_name != last_name: user.last_name = last_name; needs_update = True
            if user.email != email.lower(): user.email = email.lower(); needs_update = True
            if user.username != username: user.username = username; needs_update = True
            if not bcrypt.check_password_hash(user.password_hash, password):
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 needs_update = True
            if needs_update:
                 _db.session.commit()
                 _db.session.refresh(user)

        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    """Logs in the primary test user."""
    login_resp = client.post('/api/auth/login', json={
        'email': test_user["user_obj"].email,
        'password': test_user["password"]
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.get_data(as_text=True)}"
    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200, "CSRF token fetch failed"
    csrf_token = csrf_resp.get_json().get('csrf_token')
    assert csrf_token is not None, "CSRF token missing"
    yield client, csrf_token # Yield client and token


# --- Test Cases ---

# --- Success Scenarios ---

def test_update_profile_names_success(app, db, logged_in_client, test_user):
    """Tests successfully updating first and last names."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    original_username = test_user["user_obj"].username
    new_first_name = "UpdatedFirst"
    new_last_name = "UpdatedLast"

    payload = {
        "first_name": new_first_name,
        "last_name": new_last_name,
        "username": original_username # Keep original username
    }

    response = client.put(
        "/api/auth/profile/update",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 200
    assert "Profile updated successfully" in json_response.get("message", "")
    assert json_response["user"]["first_name"] == new_first_name
    assert json_response["user"]["last_name"] == new_last_name
    assert json_response["user"]["username"] == original_username

    # Verify DB
    with app.app_context():
        updated_user = _db.session.get(User, user_id)
        assert updated_user.first_name == new_first_name
        assert updated_user.last_name == new_last_name
        assert updated_user.username == original_username


def test_update_profile_add_username_success(app, db, logged_in_client, test_user):
    """Tests successfully adding a username when none existed."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    # --- Fetch original names BEFORE the modification block ---
    original_first_name = test_user["user_obj"].first_name
    original_last_name = test_user["user_obj"].last_name
    # --- End Fetch ---

    # Ensure user starts without a username for this test
    with app.app_context():
        user = _db.session.get(User, user_id)
        if user: # Check if user was found
            user.username = None
            _db.session.commit()
        else:
            pytest.fail(f"User with ID {user_id} not found in DB for setup.")


    new_username = f"added_username_{secrets.token_hex(4)}"
    payload = {
        "first_name": original_first_name, # Use fetched original name
        "last_name": original_last_name,   # Use fetched original name
        "username": new_username
    }

    response = client.put("/api/auth/profile/update", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()

    assert response.status_code == 200
    assert json_response["user"]["username"] == new_username

    with app.app_context():
        updated_user = _db.session.get(User, user_id)
        assert updated_user.username == new_username


def test_update_profile_change_username_success(app, db, logged_in_client, test_user):
    """Tests successfully changing an existing username."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    new_username = f"changed_username_{secrets.token_hex(4)}"
    payload = {
        "first_name": test_user["user_obj"].first_name,
        "last_name": test_user["user_obj"].last_name,
        "username": new_username
    }

    response = client.put("/api/auth/profile/update", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()

    assert response.status_code == 200
    assert json_response["user"]["username"] == new_username

    with app.app_context():
        updated_user = _db.session.get(User, user_id)
        assert updated_user.username == new_username


def test_update_profile_remove_username_success(app, db, logged_in_client, test_user):
    """Tests successfully removing an existing username."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    # Ensure user starts with a username
    with app.app_context():
        user = _db.session.get(User, user_id)
        if user and not user.username: # Check user exists before accessing username
             user.username = f"temp_username_{secrets.token_hex(4)}"
             _db.session.commit()
        elif not user:
             pytest.fail(f"User with ID {user_id} not found in DB for setup.")


    payload = {
        "first_name": test_user["user_obj"].first_name,
        "last_name": test_user["user_obj"].last_name,
        "username": "" # Send empty string to remove
    }

    response = client.put("/api/auth/profile/update", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()

    assert response.status_code == 200
    assert json_response["user"]["username"] is None

    with app.app_context():
        updated_user = _db.session.get(User, user_id)
        assert updated_user.username is None


# --- Failure Scenarios (Validation - 400) ---

@pytest.mark.parametrize("field_to_make_empty", ["first_name", "last_name"])
def test_update_profile_empty_required_field(logged_in_client, test_user, field_to_make_empty):
    """Tests failure when required name fields are empty."""
    client, csrf_token = logged_in_client
    payload = {
        "first_name": test_user["user_obj"].first_name,
        "last_name": test_user["user_obj"].last_name,
        "username": test_user["user_obj"].username
    }
    payload[field_to_make_empty] = "   " # Set to whitespace

    response = client.put("/api/auth/profile/update", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()

    assert response.status_code == 400
    assert "Validation failed" in json_response.get("error", "")
    assert field_to_make_empty in json_response.get("details", {})
    assert "cannot be empty" in json_response["details"][field_to_make_empty]


def test_update_profile_invalid_json(logged_in_client):
    """Tests failure with invalid JSON payload."""
    client, csrf_token = logged_in_client
    response = client.put(
        "/api/auth/profile/update",
        data="this is not json", # Send invalid data
        headers={"X-CSRF-TOKEN": csrf_token, "Content-Type": "application/json"}
    )

    assert response.status_code == 400
    # --- Check response data, allowing for non-JSON body ---
    try:
        # Try to get JSON, but don't fail if it's not there for this specific error
        json_response = response.get_json()
        if json_response:
             # If JSON *is* returned, check the error message
             # Check variations of the error message Flask might return
             error_msg = json_response.get("error", json_response.get("message", "")).lower()
             assert "invalid json" in error_msg or "failed to decode json" in error_msg
        else:
             # If no JSON body, check the raw response data (might be HTML or plain text)
             response_text = response.get_data(as_text=True)
             assert "json" in response_text.lower() or "bad request" in response_text.lower()
             print(f"WARN: Received non-JSON 400 response for invalid JSON: {response_text[:100]}...") # Log for info
    except Exception as e:
        pytest.fail(f"Error processing response for invalid JSON test: {e}")
    # --- End Check ---


# --- Failure Scenarios (Conflict - 409) ---

def test_update_profile_duplicate_username(app, db, logged_in_client, test_user, test_user_2):
    """Tests failure when trying to update username to one already taken."""
    client, csrf_token = logged_in_client
    user_1_id = test_user["user_obj"].id
    user_2_username = test_user_2["user_obj"].username # Username known to exist

    payload = {
        "first_name": test_user["user_obj"].first_name,
        "last_name": test_user["user_obj"].last_name,
        "username": user_2_username # Attempt to use existing username
    }

    response = client.put("/api/auth/profile/update", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()

    # --- Expecting 409 based on backend logic adjustment ---
    assert response.status_code == 409
    assert "Username is already taken" in json_response.get("error", "")
    assert json_response.get("type") == "DUPLICATE_USERNAME"
    # --- End Expectation ---

    # Verify user 1's username was not changed
    with app.app_context():
        user1 = _db.session.get(User, user_1_id)
        # Fetch original username again in case fixture reused object
        original_username = test_user["user_obj"].username
        assert user1.username == original_username # Check it hasn't changed to user_2's


# --- Failure Scenarios (Authentication - 401) ---

def test_update_profile_not_logged_in(client, test_user):
    """Tests failure when attempting update without being logged in."""
    # Ensure client is logged out
    with client.session_transaction() as sess:
        sess.clear()

    payload = {
        "first_name": "No",
        "last_name": "Auth",
        "username": "no_auth_user"
    }
    response = client.put("/api/auth/profile/update", json=payload) # No CSRF token needed if not logged in

    assert response.status_code == 401 # Expecting unauthorized
    json_response = response.get_json()
    # --- Adjust assertion based on actual 401 response ---
    assert json_response is not None, "401 response body was unexpectedly None."
    # Check common keys for the error message from @login_required or framework
    error_msg = json_response.get("error", json_response.get("msg", json_response.get("message", ""))).lower()
    assert "authentication required" in error_msg or "unauthorized" in error_msg
    # --- End Adjustment ---