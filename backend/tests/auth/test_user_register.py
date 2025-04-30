# backend/tests/auth/test_user_register.py

# --- Imports ---
import pytest
from backend.models import User
from backend import db
import secrets

# --- Fixtures ---
@pytest.fixture
def new_user_data():
    """Provides data for a new user registration."""
    unique_part = secrets.token_hex(4)
    compliant_password = "StrongPass1!" # Meets complexity rules
    return {
        # Add required first_name and last_name
        "first_name": "Test",
        "last_name": f"User_{unique_part}",
        # Keep username for testing optional field handling and uniqueness
        "username": f"newuser_session_{unique_part}",
        "email": f"test_{unique_part}@example.com",
        "password": compliant_password,
        "confirmation": compliant_password
    }

# --- Helper: Cleanup Function ---
def cleanup_user(app, email=None, username=None):
    """Removes users by email or username to ensure clean test state."""
    with app.app_context():
        users_to_delete = []
        if email:
            user_by_email = db.session.query(User).filter(User.email == email.lower()).first()
            if user_by_email:
                users_to_delete.append(user_by_email)
        if username:
             user_by_username = db.session.query(User).filter(User.username == username).first()
             # Avoid adding the same user twice if found by both email and username
             if user_by_username and user_by_username not in users_to_delete:
                 users_to_delete.append(user_by_username)

        if users_to_delete:
            for user in users_to_delete:
                # print(f"Cleaning up user: ID={user.id}, Email={user.email}, Username={user.username}") # Debugging line
                db.session.delete(user)
            db.session.commit()
        # else:
            # print(f"No user found for cleanup with Email={email}, Username={username}") # Debugging line


# --- Test Functions ---

# --- Success Case ---
def test_register_user_success(client, app, new_user_data):
    """Tests successful user registration."""
    # Ensure clean state before test
    cleanup_user(app, email=new_user_data['email'], username=new_user_data['username'])

    response = client.post(
        "/api/auth/register",
        json=new_user_data,
        headers={"Content-Type": "application/json"}
    )

    # --- Assert Response ---
    assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.get_data(as_text=True)}"
    data = response.get_json()
    assert data is not None
    assert "message" in data
    assert "user" in data
    assert data["user"]["first_name"] == new_user_data['first_name']
    assert data["user"]["last_name"] == new_user_data['last_name']
    assert data["user"]["email"] == new_user_data['email'].lower()
    assert data["user"]["username"] == new_user_data['username'] # Check optional username if provided
    assert data["user"]["id"] is not None
    assert f"user {new_user_data['first_name'].lower()} successfully registered" in data["message"].lower()


    # --- Assert Session Cookie ---
    set_cookie_headers = response.headers.getlist('Set-Cookie')
    assert any(h.strip().startswith("session=") for h in set_cookie_headers)
    session_cookie = next((h for h in set_cookie_headers if h.strip().startswith("session=")), None)
    assert session_cookie is not None
    assert "Path=/" in session_cookie
    assert "HttpOnly" in session_cookie
    assert "SameSite=Lax" in session_cookie # Or Strict depending on your config
    is_secure = app.config.get('SESSION_COOKIE_SECURE', False)
    assert ("Secure" in session_cookie) == is_secure

    # --- Assert Database State ---
    with app.app_context():
        user = db.session.query(User).filter_by(email=new_user_data["email"].lower()).first()
        assert user is not None
        assert user.first_name == new_user_data["first_name"]
        assert user.last_name == new_user_data["last_name"]
        assert user.username == new_user_data["username"]
        assert user.password_hash is not None
        assert user.is_active is True

    # Cleanup after test
    cleanup_user(app, email=new_user_data['email'])


# --- Duplicate Field Failures ---
def test_register_user_username_already_exists(client, app, new_user_data):
    """Tests registration failure when optional username is provided and already exists."""
    # Ensure clean state
    cleanup_user(app, email=new_user_data['email'], username=new_user_data['username'])
    # Ensure the second email is also clean
    second_email = f"another_{secrets.token_hex(4)}@example.com"
    cleanup_user(app, email=second_email)


    # First registration (should succeed)
    response_1 = client.post("/api/auth/register", json=new_user_data)
    assert response_1.status_code == 201, f"First registration failed: {response_1.get_data(as_text=True)}"

    # Second attempt with same username, different email
    second_attempt_data = new_user_data.copy()
    second_attempt_data["email"] = second_email # Use a different email
    # Keep first_name, last_name, username the same
    second_attempt_data["last_name"] = f"User_Dup_{secrets.token_hex(2)}" # Make last name different just in case

    response_2 = client.post("/api/auth/register", json=second_attempt_data)

    assert response_2.status_code == 409
    data = response_2.get_json()
    assert data is not None and "error" in data
    assert "username already exists" in data["error"].lower()
    assert data.get("type") == "DUPLICATE_USERNAME"

    # Cleanup
    cleanup_user(app, email=new_user_data['email'])
    cleanup_user(app, email=second_email)


def test_register_user_email_already_exists(client, app, new_user_data):
    """Tests registration failure when email already exists."""
    # Ensure clean state
    cleanup_user(app, email=new_user_data['email'], username=new_user_data['username'])
    second_username = f"another_user_{secrets.token_hex(4)}"
    cleanup_user(app, username=second_username)

    # First registration (should succeed)
    response_1 = client.post("/api/auth/register", json=new_user_data)
    assert response_1.status_code == 201, f"First registration failed: {response_1.get_data(as_text=True)}"

    # Second attempt with same email, different username
    second_attempt_data = new_user_data.copy()
    second_attempt_data["username"] = second_username # Use a different username
    # Keep email, first_name, last_name the same
    second_attempt_data["last_name"] = f"User_EmailDup_{secrets.token_hex(2)}" # Make last name different

    response_2 = client.post("/api/auth/register", json=second_attempt_data)

    assert response_2.status_code == 409
    data = response_2.get_json()
    assert data is not None and "error" in data
    assert "email address already registered" in data["error"].lower()
    assert data.get("type") == "DUPLICATE_EMAIL"

    # Cleanup
    cleanup_user(app, email=new_user_data['email']) # This should remove both attempts if username was unique


# --- Input Validation Failures ---
def test_register_passwords_do_not_match(client, app):
    """Tests registration failure when password and confirmation don't match."""
    unique_part = secrets.token_hex(4)
    payload = {
        "first_name": "Mismatch",
        "last_name": f"Pass_{unique_part}",
        "username": f"mismatchuser_{unique_part}", # Optional
        "email": f"mismatch_{unique_part}@example.com",
        "password": "abc12345!",
        "confirmation": "xyz98765!"
    }
    cleanup_user(app, email=payload['email'], username=payload['username'])

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert data is not None and "error" in data
    assert "password" in data["error"].lower() and "match" in data["error"].lower()


# --- Updated Missing/Empty Field Tests ---
@pytest.mark.parametrize("field_to_remove, expected_missing", [
    ("first_name", "first_name"),
    ("last_name", "last_name"),
    ("email", "email"),
    ("password", "password"),
    ("confirmation", "confirmation"),
])
def test_register_missing_required_fields(client, app, new_user_data, field_to_remove, expected_missing):
    """Tests registration failure when a required field is missing."""
    payload = new_user_data.copy()
    del payload[field_to_remove] # Remove the specific required field

    # Clean up potential conflicting user from base data
    cleanup_user(app, email=new_user_data['email'], username=new_user_data['username'])

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400, f"Test case: missing {field_to_remove}"
    data = response.get_json()
    assert data is not None and "error" in data
    error_msg = data["error"]
    assert f"Missing required fields: {expected_missing}" in error_msg


@pytest.mark.parametrize("field_to_empty, expected_error_msg", [
    ("first_name", "First name and last name cannot be empty."),
    ("last_name", "First name and last name cannot be empty."),
    ("email", "Missing required fields: email"), # Empty email treated as missing by route
    ("password", "Missing required fields: password"), # Empty password treated as missing
    ("confirmation", "Missing required fields: confirmation"), # Empty confirmation treated as missing
])
def test_register_empty_required_fields(client, app, new_user_data, field_to_empty, expected_error_msg):
    """Tests registration failure when a required field is empty or just whitespace."""
    payload = new_user_data.copy()
    payload[field_to_empty] = "   " if field_to_empty in ["first_name", "last_name"] else "" # Set field to empty/whitespace

    # Clean up potential conflicting user from base data
    cleanup_user(app, email=new_user_data['email'], username=new_user_data['username'])

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400, f"Test case: empty {field_to_empty}"
    data = response.get_json()
    assert data is not None and "error" in data
    assert expected_error_msg in data["error"]


# --- Invalid Email Format Test (Updated Payload) ---
@pytest.mark.parametrize("invalid_email", [
    "plainaddress", "@missingusername.com", "username@.com", "username@domain.",
    "username @domain.com", "username@domain com", "username@domain..com",
    ".username@domain.com", "username.@domain.com",
])
def test_register_invalid_email_format(client, app, invalid_email):
    """Tests registration failure with various invalid email formats."""
    unique_part = secrets.token_hex(4)
    compliant_password = "StrongPass1!"
    payload = {
        "first_name": "Invalid",
        "last_name": f"Email_{unique_part}",
        "username": f"invalidemail_{unique_part}", # Optional
        "email": invalid_email,
        "password": compliant_password,
        "confirmation": compliant_password
    }
    # Clean up potential conflicting user
    cleanup_user(app, email=payload['email'], username=payload['username'])

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400, f"Failed for email: {invalid_email}"
    data = response.get_json()
    assert data is not None and "error" in data
    assert "invalid email address format" in data["error"].lower()

# --- Password Strength Test (Add if not already covered elsewhere) ---
def test_register_weak_password(client, app, new_user_data):
    """Tests registration failure with a password that fails strength validation."""
    payload = new_user_data.copy()
    payload["password"] = "weak"
    payload["confirmation"] = "weak"

    cleanup_user(app, email=payload['email'], username=payload['username'])

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert data is not None
    assert "error" in data
    assert "password does not meet security requirements" in data["error"].lower()
    assert data.get("type") == "VALIDATION_ERROR"
    assert "details" in data # Check that specific reasons are provided
    assert isinstance(data["details"], list)
    assert len(data["details"]) > 0