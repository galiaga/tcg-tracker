# backend/tests/auth/test_user_register.py

import pytest
from backend.models import User
from backend import db
import secrets # Used for generating unique emails/usernames in tests

# --- Fixtures ---

@pytest.fixture
def new_user_data():
    """Provides data for a new user registration, including email."""
    # Use secrets to generate unique parts to avoid collisions between test runs
    unique_part = secrets.token_hex(4)
    return {
        "username": f"newuser_session_{unique_part}",
        "email": f"test_{unique_part}@example.com", # Add email
        "password": "strongpass123",
        "confirmation": "strongpass123"
    }

# --- Test Functions ---

def test_register_user_success(client, app, new_user_data):
    """Tests successful user registration including email storage."""
    with app.app_context():
        # Ensure user doesn't exist before test
        user_to_delete = db.session.query(User).filter_by(username=new_user_data['username']).first()
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
        email_to_delete = db.session.query(User).filter_by(email=new_user_data['email']).first()
        if email_to_delete:
             db.session.delete(email_to_delete)
             db.session.commit()

        response = client.post(
            "/api/auth/register",
            json=new_user_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.get_data(as_text=True)}"

        data = response.get_json()
        assert data is not None
        assert "message" in data
        assert data["username"] == new_user_data['username']
        assert "registered and logged in" in data["message"].lower()

        # Check session cookie headers (same as before)
        set_cookie_headers = response.headers.getlist('Set-Cookie')
        assert any(h.strip().startswith("session=") for h in set_cookie_headers)
        session_cookie = next((h for h in set_cookie_headers if h.strip().startswith("session=")), None)
        assert session_cookie is not None
        assert "Path=/" in session_cookie
        assert "HttpOnly" in session_cookie
        assert "SameSite=Lax" in session_cookie
        is_secure = app.config.get('SESSION_COOKIE_SECURE', False)
        assert ("Secure" in session_cookie) == is_secure

        # Verify user exists in DB and email is stored correctly (lowercase)
        user = db.session.query(User).filter_by(username=new_user_data["username"]).first()
        assert user is not None
        assert user.email == new_user_data["email"].lower() # Verify email stored lowercase
        assert user.password_hash is not None # Check password hash exists


def test_register_user_username_already_exists(client, app, new_user_data):
    """Tests registration failure when username is already taken."""
    with app.app_context():
        # Ensure user/email doesn't exist initially
        user_to_delete = db.session.query(User).filter_by(username=new_user_data['username']).first()
        if user_to_delete: db.session.delete(user_to_delete)
        email_to_delete = db.session.query(User).filter_by(email=new_user_data['email']).first()
        if email_to_delete: db.session.delete(email_to_delete)
        db.session.commit()

        # First registration (should succeed)
        response_1 = client.post("/api/auth/register", json=new_user_data)
        assert response_1.status_code == 201, f"First registration failed: {response_1.get_data(as_text=True)}"

        # Second attempt with same username (different email to isolate username conflict)
        second_attempt_data = new_user_data.copy()
        second_attempt_data["email"] = f"another_{secrets.token_hex(4)}@example.com"
        response_2 = client.post("/api/auth/register", json=second_attempt_data)

        # Expect 409 Conflict for duplicate username
        assert response_2.status_code == 409
        data = response_2.get_json()
        assert data is not None and "error" in data
        assert "username already exists" in data["error"].lower()
        assert data.get("type") == "DUPLICATE_USERNAME"


def test_register_user_email_already_exists(client, app, new_user_data):
    """Tests registration failure when email is already registered."""
    with app.app_context():
         # Ensure user/email doesn't exist initially
        user_to_delete = db.session.query(User).filter_by(username=new_user_data['username']).first()
        if user_to_delete: db.session.delete(user_to_delete)
        email_to_delete = db.session.query(User).filter_by(email=new_user_data['email']).first()
        if email_to_delete: db.session.delete(email_to_delete)
        db.session.commit()

        # First registration (should succeed)
        response_1 = client.post("/api/auth/register", json=new_user_data)
        assert response_1.status_code == 201, f"First registration failed: {response_1.get_data(as_text=True)}"

        # Second attempt with same email (different username)
        second_attempt_data = new_user_data.copy()
        second_attempt_data["username"] = f"another_user_{secrets.token_hex(4)}"
        # Use the SAME email as the first registration
        second_attempt_data["email"] = new_user_data["email"]
        response_2 = client.post("/api/auth/register", json=second_attempt_data)

        # Expect 409 Conflict for duplicate email
        assert response_2.status_code == 409
        data = response_2.get_json()
        assert data is not None and "error" in data
        assert "email address already registered" in data["error"].lower()
        assert data.get("type") == "DUPLICATE_EMAIL"


def test_register_passwords_do_not_match(client, app):
    """Tests registration failure when password and confirmation don't match."""
    with app.app_context():
        unique_part = secrets.token_hex(4)
        response = client.post(
            "/api/auth/register",
            json={
                "username": f"mismatchuser_{unique_part}",
                "email": f"mismatch_{unique_part}@example.com", # Add email
                "password": "abc12345",
                "confirmation": "xyz98765" # Mismatched password
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data is not None and "error" in data
        assert "password" in data["error"].lower() and "match" in data["error"].lower()


@pytest.mark.parametrize("payload, missing_field_desc", [
    ({"email": "test@example.com", "password": "abc", "confirmation": "abc"}, "missing username"),
    ({"username": "noemail", "password": "abc", "confirmation": "abc"}, "missing email"), # Added missing email case
    ({"username": "nouser", "email": "test@example.com", "confirmation": "abc"}, "missing password"),
    ({"username": "nouser", "email": "test@example.com", "password": "abc"}, "missing confirmation"),
    ({"username": "", "email": "test@example.com", "password": "abc", "confirmation": "abc"}, "empty username"),
    ({"username": "noemail", "email": "", "password": "abc", "confirmation": "abc"}, "empty email"), # Added empty email case
    ({"username": "nouser", "email": "test@example.com", "password": "", "confirmation": ""}, "empty password"),
])
def test_register_missing_or_empty_fields(client, app, payload, missing_field_desc):
    """Tests registration failure when required fields are missing or empty."""
    with app.app_context():
        # Ensure username/email from payload don't exist if they are non-empty
        if payload.get("username"):
            user_to_delete = db.session.query(User).filter_by(username=payload['username']).first()
            if user_to_delete: db.session.delete(user_to_delete)
        if payload.get("email"):
             email_to_delete = db.session.query(User).filter_by(email=payload['email']).first()
             if email_to_delete: db.session.delete(email_to_delete)
        db.session.commit()

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 400, f"Test case: {missing_field_desc}"
        data = response.get_json()
        assert data is not None and "error" in data
        error_msg = data["error"].lower()
        # Check against the updated required fields message
        assert "username, email, password, and confirmation are required" in error_msg


@pytest.mark.parametrize("invalid_email", [
    "plainaddress",
    "@missingusername.com",
    "username@.com",
    "username@domain.",
    "username @domain.com",
    "username@domain com",
    "username@domain..com",
    ".username@domain.com",
    "username.@domain.com",
])
def test_register_invalid_email_format(client, app, invalid_email):
    """Tests registration failure with various invalid email formats."""
    with app.app_context():
        unique_part = secrets.token_hex(4)
        payload = {
            "username": f"invalidemail_{unique_part}",
            "email": invalid_email, # Use the parametrized invalid email
            "password": "strongpassword123",
            "confirmation": "strongpassword123"
        }

        # Ensure username/email don't exist
        user_to_delete = db.session.query(User).filter_by(username=payload['username']).first()
        if user_to_delete: db.session.delete(user_to_delete)
        email_to_delete = db.session.query(User).filter_by(email=payload['email']).first()
        if email_to_delete: db.session.delete(email_to_delete)
        db.session.commit()

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 400, f"Failed for email: {invalid_email}"
        data = response.get_json()
        assert data is not None and "error" in data
        assert "invalid email address format" in data["error"].lower()