import pytest
from backend.models import User
from backend import db

@pytest.fixture
def new_user_data():
    return {
        "username": "newuser_session",
        "password": "strongpass123",
        "confirmation": "strongpass123"
    }

def test_register_user_success(client, app, new_user_data):
    with app.app_context():
        response = client.post(
            "/api/auth/register",
            json=new_user_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 201

        data = response.get_json()
        assert data is not None
        assert "message" in data
        assert data["username"] == new_user_data['username']
        assert "registered and logged in" in data["message"].lower()

        set_cookie_headers = response.headers.getlist('Set-Cookie')
        assert any(h.strip().startswith("session=") for h in set_cookie_headers)

        session_cookie = next((h for h in set_cookie_headers if h.strip().startswith("session=")), None)
        assert session_cookie is not None
        assert "Path=/" in session_cookie
        assert "HttpOnly" in session_cookie
        assert "SameSite=Lax" in session_cookie # Or Strict depending on your config

        is_secure = app.config.get('SESSION_COOKIE_SECURE', False)
        assert ("Secure" in session_cookie) == is_secure

        # Verify user exists in DB
        user = db.session.query(User).filter_by(username=new_user_data["username"]).first()
        assert user is not None


def test_register_user_already_exists(client, app, new_user_data):
    with app.app_context():
        user_to_delete = db.session.query(User).filter_by(username=new_user_data['username']).first()
        if user_to_delete:
            print(f"DEBUG: Deleting existing user '{new_user_data['username']}' before test.")
            db.session.delete(user_to_delete)
            db.session.commit()

        response_1 = client.post("/api/auth/register", json=new_user_data)
        if response_1.status_code != 201:
            print(f"DEBUG: First registration STILL failed! Status: {response_1.status_code}")
            try:
                print(f"DEBUG: Response body: {response_1.get_json()}")
            except:
                print(f"DEBUG: Response body: (not json)")
        assert response_1.status_code == 201

        response_2 = client.post("/api/auth/register", json=new_user_data)

        assert response_2.status_code in [400, 409] 
        data = response_2.get_json()
        assert data is not None and "error" in data
        error_msg = data["error"].lower()
        assert "username already exists" in error_msg or "already exists" in error_msg


def test_register_passwords_do_not_match(client, app):
    with app.app_context():
        response = client.post(
            "/api/auth/register",
            json={
                "username": "mismatchuser_session",
                "password": "abc12345",
                "confirmation": "xyz98765"
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data is not None and "error" in data
        assert "password" in data["error"].lower() and "match" in data["error"].lower()


@pytest.mark.parametrize("payload, missing_field_desc", [
    ({"password": "abc", "confirmation": "abc"}, "missing username"),
    ({"username": "nouser_session", "confirmation": "abc"}, "missing password"),
    ({"username": "nouser_session", "password": "abc"}, "missing confirmation"),
    ({"username": "", "password": "abc", "confirmation": "abc"}, "empty username"),
    ({"username": "nouser_session", "password": "", "confirmation": ""}, "empty password"),
])
def test_register_missing_or_empty_fields(client, app, payload, missing_field_desc):
    with app.app_context():
        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data is not None and "error" in data
        error_msg = data["error"].lower()
        assert "required" in error_msg or "empty" in error_msg or "missing" in error_msg