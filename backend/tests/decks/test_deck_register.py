import pytest
from flask import Flask
from backend import create_app, db
from backend.models import Commander, Deck
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token, JWTManager
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
jwt = JWTManager()

@pytest.fixture
def app():
    app = create_app("testing") 

    bcrypt.init_app(app)    
    jwt.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()

def test_invalid_partner_combination(client, app):
    with app.app_context():
        from backend.models import User
        hashed_password = bcrypt.generate_password_hash("123").decode("utf-8")
        user = User(username="testuser", hash=hashed_password)
        db.session.add(user)
        db.session.commit()

        commander = Commander(name="Main Commander", partner=False, scryfall_id="abc123")
        partner = Commander(name="Invalid Partner", partner=True, scryfall_id="def456")
        db.session.add_all([commander, partner])
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = client.post("/api/register_deck",
            json={
                "deck_name": "Test Deck",
                "deck_type": 7,
                "commander_id": commander.id,
                "partner_id": partner.id
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )

        print("🧪 RESPONSE:", response.status_code, response.get_json())

        assert response.status_code == 400
        assert "not a valid" in response.get_json()["error"]