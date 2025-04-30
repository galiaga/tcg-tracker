# backend/tests/auth/test_profile_actions.py

# --- Imports ---
import pytest
import secrets
from flask_bcrypt import Bcrypt
from sqlalchemy import select
from backend import db as _db # Use alias
from backend.models import User

# --- Fixtures ---

bcrypt = Bcrypt()

@pytest.fixture(scope='function')
def test_user(app, db):
    """Creates or retrieves the test user for profile actions."""
    email = "profileaction@example.com"
    first_name = "Action"
    last_name = "User"
    username = f"action_user_{secrets.token_hex(4)}"
    password = "Password_current1!" # Use a compliant password
    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user: user = _db.session.scalar(select(User).where(User.username == username))

        if not user:
            print(f"\nDEBUG: Creating user for profile action tests: {email}")
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email.lower(),
                username=username,
                password_hash=hashed_password,
                is_active=True, # Ensure user is active
                deleted_at=None
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        else:
            print(f"\nDEBUG: Found existing user for profile action tests: {user.email}")
            needs_update = False
            if not user.is_active or user.deleted_at: # Ensure user is active for tests
                 user.is_active = True
                 user.deleted_at = None
                 needs_update = True
            if user.first_name != first_name: user.first_name = first_name; needs_update = True
            if user.last_name != last_name: user.last_name = last_name; needs_update = True
            if user.email != email.lower(): user.email = email.lower(); needs_update = True
            if not user.username: user.username = username; needs_update = True # Ensure username exists if needed
            if not bcrypt.check_password_hash(user.password_hash, password):
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 needs_update = True
            if needs_update:
                 _db.session.commit()
                 _db.session.refresh(user)

        yield {"user_obj": user, "password": password}

@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    """Logs in the test user."""
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


# --- Test Cases: Change Password ---

def test_change_password_success(app, db, logged_in_client, test_user):
    """Tests successfully changing the password."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    current_password = test_user["password"]
    new_password = "NewPassword123!"

    payload = {
        "current_password": current_password,
        "new_password": new_password,
        "confirmation": new_password
    }
    response = client.put(
        "/api/auth/profile/change-password",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 200
    assert "Password changed successfully" in json_response.get("message", "")

    # Verify password hash changed in DB
    with app.app_context():
        updated_user = _db.session.get(User, user_id)
        assert updated_user is not None
        assert bcrypt.check_password_hash(updated_user.password_hash, new_password)
        assert not bcrypt.check_password_hash(updated_user.password_hash, current_password)


def test_change_password_incorrect_current(app, db, logged_in_client, test_user):
    """Tests failure when providing the wrong current password."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    original_hash = test_user["user_obj"].password_hash
    new_password = "NewPassword123!"

    payload = {
        "current_password": "wrong_password", # Incorrect current password
        "new_password": new_password,
        "confirmation": new_password
    }
    response = client.put(
        "/api/auth/profile/change-password",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 400 # Or 403 depending on backend choice
    assert "Incorrect current password" in json_response.get("error", "")
    assert json_response.get("type") == "INVALID_CURRENT_PASSWORD"

    # Verify password hash DID NOT change
    with app.app_context():
        user = _db.session.get(User, user_id)
        assert user.password_hash == original_hash


def test_change_password_mismatched_new(app, db, logged_in_client, test_user):
    """Tests failure when new password and confirmation don't match."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    original_hash = test_user["user_obj"].password_hash

    payload = {
        "current_password": test_user["password"],
        "new_password": "NewPassword123!",
        "confirmation": "DoesNotMatch456!" # Mismatched confirmation
    }
    response = client.put(
        "/api/auth/profile/change-password",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 400
    assert "New passwords do not match" in json_response.get("error", "")
    assert json_response.get("type") == "PASSWORD_MISMATCH"

    # Verify password hash DID NOT change
    with app.app_context():
        user = _db.session.get(User, user_id)
        assert user.password_hash == original_hash


def test_change_password_weak_new(app, db, logged_in_client, test_user):
    """Tests failure when new password fails complexity validation."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    original_hash = test_user["user_obj"].password_hash

    payload = {
        "current_password": test_user["password"],
        "new_password": "weak", # Fails complexity
        "confirmation": "weak"
    }
    response = client.put(
        "/api/auth/profile/change-password",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 400
    assert "does not meet security requirements" in json_response.get("error", "")
    assert json_response.get("type") == "WEAK_PASSWORD"
    assert "details" in json_response

    # Verify password hash DID NOT change
    with app.app_context():
        user = _db.session.get(User, user_id)
        assert user.password_hash == original_hash


def test_change_password_same_as_old(app, db, logged_in_client, test_user):
    """Tests failure when new password is the same as the current one."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    original_hash = test_user["user_obj"].password_hash
    current_password = test_user["password"]

    payload = {
        "current_password": current_password,
        "new_password": current_password, # Same as current
        "confirmation": current_password
    }
    response = client.put(
        "/api/auth/profile/change-password",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 400
    assert "cannot be the same as the current password" in json_response.get("error", "")
    assert json_response.get("type") == "PASSWORD_SAME_AS_OLD"

    # Verify password hash DID NOT change
    with app.app_context():
        user = _db.session.get(User, user_id)
        assert user.password_hash == original_hash


def test_change_password_missing_fields(logged_in_client):
    """Tests failure when required fields are missing."""
    client, csrf_token = logged_in_client
    payload = {"new_password": "NewPassword123!", "confirmation": "NewPassword123!"} # Missing current_password
    response = client.put("/api/auth/profile/change-password", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 400
    assert "required" in response.get_json().get("error", "")


def test_change_password_not_logged_in(client):
    """Tests failure when attempting change password without being logged in."""
    with client.session_transaction() as sess: sess.clear()
    payload = {"current_password": "a", "new_password": "b", "confirmation": "b"}
    response = client.put("/api/auth/profile/change-password", json=payload)
    assert response.status_code == 401


# --- Test Cases: Delete Account ---

def test_delete_account_success(app, db, logged_in_client, test_user):
    """Tests successfully deactivating (soft deleting) the account."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    password = test_user["password"]

    payload = {"password": password}
    response = client.delete(
        "/api/auth/profile/delete",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 200
    assert "Account deactivated successfully" in json_response.get("message", "")

    # Verify user is inactive in DB
    with app.app_context():
        deleted_user = _db.session.get(User, user_id)
        assert deleted_user is not None
        assert deleted_user.is_active is False
        assert deleted_user.deleted_at is not None

    # Verify session was cleared by trying an authenticated request
    response_check = client.get('/api/auth/profile') # Request profile info
    assert response_check.status_code == 401 # Should fail as session is cleared


def test_delete_account_incorrect_password(app, db, logged_in_client, test_user):
    """Tests failure when providing the wrong password for deletion confirmation."""
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id

    payload = {"password": "wrong_password"} # Incorrect password
    response = client.delete(
        "/api/auth/profile/delete",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 403 # Expecting Forbidden
    assert "Incorrect password provided" in json_response.get("error", "")
    assert json_response.get("type") == "INVALID_PASSWORD"

    # Verify user is still active in DB
    with app.app_context():
        user = _db.session.get(User, user_id)
        assert user is not None
        assert user.is_active is True
        assert user.deleted_at is None


def test_delete_account_missing_password(logged_in_client):
    """Tests failure when password confirmation is missing."""
    client, csrf_token = logged_in_client
    # --- Send valid JSON, but without the 'password' key ---
    payload = {"some_other_key": "value"}
    # --- End Change ---
    response = client.delete(
        "/api/auth/profile/delete",
        json=payload, # Send the modified payload
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    json_response = response.get_json()
    assert json_response is not None # Ensure JSON was returned
    assert "Password confirmation is required" in json_response.get("error", "")


def test_delete_account_not_logged_in(client):
    """Tests failure when attempting delete account without being logged in."""
    with client.session_transaction() as sess: sess.clear()
    payload = {"password": "any_password"}
    response = client.delete("/api/auth/profile/delete", json=payload)
    assert response.status_code == 401