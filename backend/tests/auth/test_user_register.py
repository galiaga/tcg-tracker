import pytest

@pytest.fixture
def new_user_data():
    return {
        "username": "newuser",
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

        print("✅ RESPONSE:", response.status_code, response.get_json())

        assert response.status_code == 201
        data = response.get_json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)

def test_register_user_already_exists(client, app, new_user_data):
    with app.app_context():
        # Primer intento debe funcionar
        response_1 = client.post(
            "/api/auth/register",
            json=new_user_data,
            headers={"Content-Type": "application/json"}
        )
        assert response_1.status_code == 201

        # Segundo intento con mismo username debe fallar
        response_2 = client.post(
            "/api/auth/register",
            json=new_user_data,
            headers={"Content-Type": "application/json"}
        )

        print("⚠️ RESPONSE:", response_2.status_code, response_2.get_json())

        assert response_2.status_code == 400 or response_2.status_code == 409
        data = response_2.get_json()
        assert "error" in data
        assert "username" in data["error"].lower() or "already" in data["error"].lower()


def test_register_passwords_do_not_match(client, app):
    with app.app_context():
        response = client.post(
            "/api/auth/register",
            json={
                "username": "mismatchuser",
                "password": "abc12345",
                "confirmation": "xyz98765"  # <– no coinciden
            },
            headers={"Content-Type": "application/json"}
        )

        print("❌ RESPONSE:", response.status_code, response.get_json())

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "password" in data["error"].lower()


@pytest.mark.parametrize("payload, missing_field", [
    ({"password": "abc123", "confirmation": "abc123"}, "username"),
    ({"username": "nouser", "confirmation": "abc123"}, "password"),
    ({"username": "nouser", "password": "abc123"}, "confirmation"),
])
def test_register_missing_fields(client, app, payload, missing_field):
    with app.app_context():
        response = client.post(
            "/api/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"🚫 Missing {missing_field} →", response.status_code, response.get_json())

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "required" in data["error"].lower()