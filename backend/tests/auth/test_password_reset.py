# backend/tests/auth/test_password_reset.py

# --- Imports ---
import pytest
import secrets
import time
from unittest.mock import MagicMock, patch
from itsdangerous import SignatureExpired
from backend import db, bcrypt
from backend.models import User
from backend.utils.validation import validate_password_strength_backend

# --- Fixtures ---
@pytest.fixture(scope="function")
def test_user(app):
    with app.app_context():
        unique_part = secrets.token_hex(4)
        username = f"reset_user_{unique_part}"
        email = f"reset_{unique_part}@example.com"
        password = "InitialPass1!"
        try:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(username=username, email=email.lower(), password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            print(f"\nDEBUG: Created test user {user.id}: {user.username} / {user.email}")
        except Exception as e:
            db.session.rollback()
            pytest.fail(f"Failed to create test user: {e}")
        yield user
        try:
            user_to_delete = db.session.get(User, user.id)
            if user_to_delete:
                db.session.delete(user_to_delete)
                db.session.commit()
                print(f"\nDEBUG: Deleted test user {user.id}: {user.username}")
        except Exception as e:
            print(f"\nWARN: Error during test user cleanup: {e}")
            db.session.rollback()

# --- Test Configuration ---
MOCK_EMAIL_PATH = 'backend.routes.auth.send_password_reset_email_manual'

# --- Tests for /api/auth/forgot-password ---
def test_forgot_password_success(client, app, test_user, mocker):
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={"email": test_user.email}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        mock_send_manual.assert_called_once()
        call_args, call_kwargs = mock_send_manual.call_args
        called_user_arg = call_args[0]
        assert isinstance(called_user_arg, User)
        assert called_user_arg.id == test_user.id

def test_forgot_password_unregistered_email(client, app, mocker):
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    non_existent_email = f"not_a_user_{secrets.token_hex(4)}@example.com"
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={"email": non_existent_email}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        mock_send_manual.assert_not_called()

def test_forgot_password_invalid_email_format(client, app, mocker):
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    invalid_email = "this-is-not-an-email"
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={"email": invalid_email}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        mock_send_manual.assert_not_called()

def test_forgot_password_missing_email(client, app, mocker):
    mock_send_manual = mocker.patch(MOCK_EMAIL_PATH)
    with app.app_context():
        response = client.post("/api/auth/forgot-password", json={}, headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.get_json()
        assert "if an account with that email exists" in data["message"].lower()
        mock_send_manual.assert_not_called()

# --- Tests for /api/auth/reset-password/<token> ---
def test_reset_password_success(client, app, test_user):
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
        updated_user = db.session.get(User, test_user.id)
        assert updated_user is not None
        assert bcrypt.check_password_hash(updated_user.password_hash, new_password)
        assert not bcrypt.check_password_hash(updated_user.password_hash, "InitialPass1!")

def test_reset_password_invalid_token(client, app, test_user):
    with app.app_context():
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
        user_check = db.session.get(User, test_user.id)
        assert bcrypt.check_password_hash(user_check.password_hash, "InitialPass1!")

def test_reset_password_expired_token_direct_check(client, app, test_user):
    with app.app_context():
        serializer = app.password_reset_serializer
        token = serializer.dumps(test_user.email, salt='password-reset-salt')
        time.sleep(1)
        with pytest.raises(SignatureExpired):
             serializer.loads(token, salt='password-reset-salt', max_age=0.5)

def test_reset_password_missing_fields(client, app, test_user):
    with app.app_context():
        serializer = app.password_reset_serializer
        token = serializer.dumps(test_user.email, salt='password-reset-salt')

        response_no_pass_key = client.post(
            f"/api/auth/reset-password/{token}",
            json={"other_field": "some_value"},
            headers={"Content-Type": "application/json"}
        )
        assert response_no_pass_key.status_code == 400
        data_no_pass_key = response_no_pass_key.get_json()
        assert "new password is required" in data_no_pass_key["error"].lower()

        response_empty_json = client.post(
            f"/api/auth/reset-password/{token}",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert response_empty_json.status_code == 400
        data_empty_json = response_empty_json.get_json()
        assert "new password is required" in data_empty_json["error"].lower()

        user_check = db.session.get(User, test_user.id)
        assert bcrypt.check_password_hash(user_check.password_hash, "InitialPass1!")

def test_reset_password_weak_password(client, app, test_user):
    with app.app_context():
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
        assert any("characters long" in detail for detail in data["details"])

        user_check = db.session.get(User, test_user.id)
        assert bcrypt.check_password_hash(user_check.password_hash, "InitialPass1!")