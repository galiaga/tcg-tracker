# backend/tests/auth/test_password_reset.py

# --- Imports ---
import pytest
import secrets
import time
from unittest.mock import MagicMock, patch
from itsdangerous import SignatureExpired, URLSafeTimedSerializer, BadTimeSignature, Signer, BadSignature
from backend import db, bcrypt # Import bcrypt from backend init
from backend.models import User
import datetime
import json

# --- Fixtures ---
@pytest.fixture(scope="function")
def test_user(app):
    """Creates a test user with required fields for password reset tests."""
    with app.app_context():
        unique_part = secrets.token_hex(4)
        # --- Updated User Creation ---
        first_name = "Reset"
        last_name = f"User_{unique_part}"
        email = f"reset_{unique_part}@example.com"
        username = f"reset_user_{unique_part}" # Keep username for completeness, though optional
        password = "InitialPass1!"
        # --- End Update ---
        user = None # Initialize user to None
        try:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            # --- Updated User Instantiation ---
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email.lower(),
                username=username, # Pass optional username
                password_hash=hashed_password
            )
            # --- End Update ---
            db.session.add(user)
            db.session.commit()
            # Use full_name for logging if available
            print(f"\nDEBUG: Created test user {user.id}: {user.full_name} / {user.email}")
        except Exception as e:
            db.session.rollback()
            pytest.fail(f"Failed to create test user: {e}")

        yield user # Provide the created user object to the test

        # --- Cleanup ---
        if user and user.id: # Check if user was successfully created and has an ID
            try:
                # Use db.session.get for efficient lookup by primary key
                user_to_delete = db.session.get(User, user.id)
                if user_to_delete:
                    db.session.delete(user_to_delete)
                    db.session.commit()
                    print(f"\nDEBUG: Deleted test user {user.id}: {user_to_delete.full_name}")
            except Exception as e:
                print(f"\nWARN: Error during test user cleanup (ID: {user.id}): {e}")
                db.session.rollback()
        else:
             print(f"\nWARN: Cleanup skipped, test user object invalid or not created.")


# --- Test Configuration ---
MOCK_EMAIL_PATH = 'backend.routes.auth.send_password_reset_email_manual'

# --- Tests for /api/auth/forgot-password ---
# These tests should remain largely the same as they focus on email existence
# and the response message, not user details beyond email.

def test_forgot_password_success(client, app, test_user, mocker):
    """Tests successful password reset request."""
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={"email": test_user.email}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        # Verify the correct user object was passed to the email function
        mock_send_manual.assert_called_once()
        call_args, call_kwargs = mock_send_manual.call_args
        called_user_arg = call_args[0]
        assert isinstance(called_user_arg, User)
        assert called_user_arg.id == test_user.id
        assert called_user_arg.email == test_user.email # Double check email matches

def test_forgot_password_unregistered_email(client, app, mocker):
    """Tests password reset request for an email not in the DB."""
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    non_existent_email = f"not_a_user_{secrets.token_hex(4)}@example.com"
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={"email": non_existent_email}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        mock_send_manual.assert_not_called() # Email shouldn't be sent

def test_forgot_password_invalid_email_format(client, app, mocker):
    """Tests password reset request with an invalid email format."""
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    invalid_email = "this-is-not-an-email"
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={"email": invalid_email}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200 # Route still returns 200 for security
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        mock_send_manual.assert_not_called()

def test_forgot_password_missing_email(client, app, mocker):
    """Tests password reset request with no email provided."""
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200 # Route still returns 200 for security
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        mock_send_manual.assert_not_called()

# --- Tests for /api/auth/reset-password/<token> ---
# These tests should also remain largely the same, focusing on token validity,
# password strength, and the final password hash update.

def test_reset_password_success(client, app, test_user):
    """Tests successfully resetting a password with a valid token."""
    with app.app_context():
        serializer = app.password_reset_serializer
        token = serializer.dumps(test_user.email, salt='password-reset-salt')
        new_password = "NewValidPass1!"
        response = client.post(
            f"/api/auth/reset-password/{token}",
            json={"password": new_password},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "password has been successfully updated" in data["message"].lower()
        # Verify password update in DB
        updated_user = db.session.get(User, test_user.id)
        assert updated_user is not None
        assert bcrypt.check_password_hash(updated_user.password_hash, new_password)
        assert not bcrypt.check_password_hash(updated_user.password_hash, "InitialPass1!") # Check old pass fails

def test_reset_password_invalid_token(client, app, test_user):
    """Tests resetting password with an invalid/malformed token."""
    with app.app_context():
        initial_password = "InitialPass1!" # Define initial password for checking
        invalid_token = "this.is.not.a.valid.token" + secrets.token_hex(10)
        new_password = "NewValidPass1!"
        response = client.post(
            f"/api/auth/reset-password/{invalid_token}",
            json={"password": new_password},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "invalid" in data["error"].lower() or "corrupted" in data["error"].lower()
        assert data.get("type") in ["TOKEN_INVALID", "TOKEN_ERROR"]
        # Verify password was NOT changed in DB
        user_check = db.session.get(User, test_user.id)
        assert bcrypt.check_password_hash(user_check.password_hash, initial_password)

def test_reset_password_expired_token_handled_by_route(client, app, test_user):
    """
    Tests that the /reset-password route correctly handles a SignatureExpired
    exception raised by the serializer's loads method.
    """
    with app.app_context():
        serializer = app.password_reset_serializer
        # Generate a token that would normally be valid if not for the patch
        token = serializer.dumps(test_user.email, salt='password-reset-salt')
        new_password = "NewValidPass1!"

        # --- Patch the 'loads' method ---
        # We target the 'loads' method of the *specific serializer instance*
        # attached to the app. We configure the patch to raise SignatureExpired
        # whenever it's called within the 'with' block.
        with patch.object(serializer, 'loads', side_effect=SignatureExpired("Simulated expiry via patch")) as mock_loads:
            print(f"\nDEBUG: Patching {serializer!r}.loads to raise SignatureExpired.")

            # Make the request to the endpoint
            response = client.post(
                f"/api/auth/reset-password/{token}",
                json={"password": new_password},
                headers={"Content-Type": "application/json"}
            )

            # --- Assertions ---
            # 1. Check that our patched 'loads' method was actually called
            mock_loads.assert_called_once()

            # 2. Check the arguments passed to the patched 'loads'
            #    The route calls it like: s.loads(token, salt='password-reset-salt', max_age=3600)
            call_args, call_kwargs = mock_loads.call_args
            assert call_args[0] == token # Check the token argument
            assert call_kwargs.get('salt') == 'password-reset-salt' # Check the salt keyword argument
            assert call_kwargs.get('max_age') == 3600 # Check the max_age used by the route

            # 3. Assert the HTTP response indicates the token expired error
            assert response.status_code == 400, f"Expected 400 for expired token, got {response.status_code}"
            data = response.get_json()
            assert data is not None
            assert "error" in data
            assert "expired" in data["error"].lower() # Check for "expired" in the error message
            assert data.get("type") == "TOKEN_EXPIRED" # Check for the specific error type

        # 4. Verify password was NOT changed in the database
        user_check = db.session.get(User, test_user.id)
        assert bcrypt.check_password_hash(user_check.password_hash, "InitialPass1!")
        print("\nDEBUG: Confirmed password was not changed in DB after simulated expiry.")

def test_reset_password_missing_fields(client, app, test_user):
    """Tests resetting password when required 'password' field is missing."""
    with app.app_context():
        initial_password = "InitialPass1!" # Define initial password for checking
        serializer = app.password_reset_serializer
        token = serializer.dumps(test_user.email, salt='password-reset-salt')

        # Test case 1: Missing 'password' key
        response_no_pass_key = client.post(
            f"/api/auth/reset-password/{token}",
            json={"other_field": "some_value"},
            headers={"Content-Type": "application/json"}
        )
        assert response_no_pass_key.status_code == 400
        data_no_pass_key = response_no_pass_key.get_json()
        assert "new password is required" in data_no_pass_key["error"].lower()

        # Test case 2: Empty JSON payload
        response_empty_json = client.post(
            f"/api/auth/reset-password/{token}",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert response_empty_json.status_code == 400
        data_empty_json = response_empty_json.get_json()
        assert "new password is required" in data_empty_json["error"].lower()

        # Verify password was NOT changed in DB
        user_check = db.session.get(User, test_user.id)
        assert bcrypt.check_password_hash(user_check.password_hash, initial_password)

def test_reset_password_weak_password(client, app, test_user):
    """Tests resetting password with a password failing strength validation."""
    with app.app_context():
        initial_password = "InitialPass1!" # Define initial password for checking
        serializer = app.password_reset_serializer
        token = serializer.dumps(test_user.email, salt='password-reset-salt')
        weak_password = "short"
        response = client.post(
            f"/api/auth/reset-password/{token}",
            json={"password": weak_password},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "password does not meet security requirements" in data["error"].lower()
        assert data.get("type") == "VALIDATION_ERROR"
        assert "details" in data
        assert isinstance(data["details"], list)
        # Check for a specific error detail expected from your validator
        assert any("characters long" in detail for detail in data["details"])

        # Verify password was NOT changed in DB
        user_check = db.session.get(User, test_user.id)
        assert bcrypt.check_password_hash(user_check.password_hash, initial_password)