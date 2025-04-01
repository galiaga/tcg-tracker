import pytest
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from backend.models import User, Deck, DeckType
from backend import db

bcrypt = Bcrypt()

@pytest.fixture
def test_user(app):
    with app.app_context():
        hashed_password = bcrypt.generate_password_hash("123").decode("utf-8")
        user = User(username="testuser", hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        return user.id

@pytest.fixture
def test_decks(app, test_user):
    with app.app_context():
        commander_type = DeckType(id=7, name="Commander / EDH")
        modern_type = DeckType(id=2, name="Modern")
        db.session.add_all([commander_type, modern_type])
        db.session.commit()

        d1 = Deck(name="Deck 1", user_id=test_user, deck_type_id=7)
        d2 = Deck(name="Deck 2", user_id=test_user, deck_type_id=2)
        db.session.add_all([d1, d2])
        db.session.commit()

        return [
            {"name": d1.name, "type": d1.deck_type_id},
            {"name": d2.name, "type": d2.deck_type_id}
        ]

def test_get_user_decks_success(client, app, test_user, test_decks):
    with app.app_context():
        access_token = create_access_token(identity=str(test_user))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/api/user_decks", headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert isinstance(data, list)
        assert len(data) == len(test_decks)

        returned_names = {d['name'] for d in data}
        expected_names = {d['name'] for d in test_decks}
        assert returned_names == expected_names

def test_get_user_decks_filter_commander(client, app, test_user, test_decks):
    with app.app_context():
        access_token = create_access_token(identity=str(test_user))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/api/user_decks?deck_type_id=7", headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["type"] == 7

def test_get_user_decks_filter_modern(client, app, test_user, test_decks):
    with app.app_context():
        access_token = create_access_token(identity=str(test_user))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/api/user_decks?deck_type_id=2", headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["type"] == 2

def test_get_user_decks_filter_all(client, app, test_user, test_decks):
    with app.app_context():
        access_token = create_access_token(identity=str(test_user))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/api/user_decks?deck_type_id=all", headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == len(test_decks)

def test_get_user_decks_filter_invalid(client, app, test_user, test_decks):
    with app.app_context():
        access_token = create_access_token(identity=str(test_user))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/api/user_decks?deck_type_id=xyz", headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == len(test_decks)

def test_get_user_decks_unauthenticated(client):
    response = client.get("/api/user_decks")
    assert response.status_code == 401
