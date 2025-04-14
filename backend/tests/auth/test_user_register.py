import pytest
import re 

@pytest.fixture
def new_user_data():
    """Provides valid data for a new user registration."""
    return {
        "username": "newuser",
        "password": "strongpass123",
        "confirmation": "strongpass123"
    }

def test_register_user_success(client, app, new_user_data):
    """Test successful user registration sets cookies and returns correct JSON."""
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
        assert "access_token" not in data 

        set_cookie_headers = response.headers.getlist('Set-Cookie')
        assert any(h.strip().startswith("access_token_cookie=") for h in set_cookie_headers)
        assert any(h.strip().startswith("csrf_access_token=") for h in set_cookie_headers)

        access_cookie = next((h for h in set_cookie_headers if h.strip().startswith("access_token_cookie=")), None)
        csrf_cookie = next((h for h in set_cookie_headers if h.strip().startswith("csrf_access_token=")), None)

        assert access_cookie is not None
        assert "Path=/" in access_cookie
        assert "HttpOnly" in access_cookie
        assert "SameSite=Lax" in access_cookie

        assert csrf_cookie is not None
        assert "Path=/" in csrf_cookie
        assert "HttpOnly" not in csrf_cookie 
        assert "SameSite=Lax" in csrf_cookie

        is_secure = not app.config.get('DEBUG', True)
        assert ("Secure" in access_cookie) == is_secure
        assert ("Secure" in csrf_cookie) == is_secure


def test_register_user_already_exists(client, app, new_user_data):
    """Test registration attempt with an existing username."""
    with app.app_context():
        response_1 = client.post("/api/auth/register", json=new_user_data)
        assert response_1.status_code == 201

        response_2 = client.post("/api/auth/register", json=new_user_data)

        assert response_2.status_code in [400, 409]
        data = response_2.get_json()
        assert "error" in data
        error_msg = data["error"].lower()
        assert "username already exists" in error_msg or "already exists" in error_msg


def test_register_passwords_do_not_match(client, app):
    """Test registration with mismatching password and confirmation."""
    with app.app_context():
        response = client.post(
            "/api/auth/register",
            json={
                "username": "mismatchuser",
                "password": "abc12345",
                "confirmation": "xyz98765" 
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "password" in data["error"].lower() and "match" in data["error"].lower()


@pytest.mark.parametrize("payload, missing_field_desc", [
    ({"password": "abc", "confirmation": "abc"}, "missing username"),
    ({"username": "nouser", "confirmation": "abc"}, "missing password"),
    ({"username": "nouser", "password": "abc"}, "missing confirmation"),
    ({"username": "", "password": "abc", "confirmation": "abc"}, "empty username"),
    ({"username": "nouser", "password": "", "confirmation": ""}, "empty password"),
])
def test_register_missing_or_empty_fields(client, app, payload, missing_field_desc):
    """Test registration with missing or empty required fields."""
    with app.app_context():
        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        error_msg = data["error"].lower()
        assert "required" in error_msg or "empty" in error_msg or "missing" in error_msg