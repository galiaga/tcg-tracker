import pytest
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt

from backend.models import User, Tag, Deck, UserDeck, DeckType
from backend import db as _db
from sqlalchemy.orm import selectinload, joinedload

@pytest.fixture(scope='function')
def test_user(app, db):
    bcrypt = Bcrypt(app)
    with app.app_context():
        user = User.query.filter_by(username="tags_testuser").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("password123").decode("utf-8")
            user = User(username="tags_testuser", hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
        yield user

@pytest.fixture(scope='function')
def test_user_2(app, db):
    bcrypt = Bcrypt(app)
    with app.app_context():
        user = User.query.filter_by(username="tags_testuser_2").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("password456").decode("utf-8")
            user = User(username="tags_testuser_2", hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
        yield user

@pytest.fixture(scope='function')
def auth_headers(test_user):
   access_token = create_access_token(identity=str(test_user.id))
   headers = {
       "Authorization": f"Bearer {access_token}",
       "Content-Type": "application/json"
   }
   return headers

@pytest.fixture(scope='function')
def auth_headers_user_2(test_user_2):
    access_token = create_access_token(identity=str(test_user_2.id))
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    return headers

@pytest.fixture(scope='function')
def sample_tags_data(app, db, test_user):
    with app.app_context():
        tags = {}
        tag_names = ["competitive", "budget", "testing"]
        for name in tag_names:
             tag = Tag.query.filter_by(user_id=test_user.id, name=name).first()
             if not tag:
                  tag = Tag(user_id=test_user.id, name=name)
                  _db.session.add(tag)
                  _db.session.commit()
             else:
                  _db.session.refresh(tag)
             tags[name] = tag.id
        yield tags


@pytest.fixture(scope='function')
def sample_deck_data(app, db, test_user):
     with app.app_context():
        deck = Deck.query.filter_by(name="Tag Test Deck", user_id=test_user.id).first()
        if not deck:
            deck_type = DeckType.query.filter_by(id=1).first()
            if not deck_type:
                deck_type = DeckType(id=1, name='Standard')
                _db.session.add(deck_type)
                _db.session.commit()

            deck = Deck(
                name="Tag Test Deck",
                deck_type_id=deck_type.id,
                user_id=test_user.id
            )
            _db.session.add(deck)
            _db.session.flush()

            user_deck = UserDeck(user_id=test_user.id, deck_id=deck.id)
            _db.session.add(user_deck)
            _db.session.commit()
        yield {"id": deck.id, "user_id": test_user.id, "name": deck.name }

@pytest.fixture(scope='function')
def deck_with_tag_data(app, db, sample_deck_data, sample_tags_data):
    with app.app_context():
        deck_id = sample_deck_data["id"]
        tag_id = sample_tags_data["competitive"]
        deck = _db.session.get(Deck, deck_id)
        tag = _db.session.get(Tag, tag_id)

        if deck and tag:
            _db.session.refresh(deck)
            if tag not in deck.tags:
                 deck.tags.append(tag)
                 _db.session.commit()
        yield {"deck_id": deck_id, "tag_id": tag_id}

def test_get_tags_success_no_tags(client, app, auth_headers, db, test_user): 
    with app.app_context():
        Tag.query.filter_by(user_id=test_user.id).delete()
        _db.session.commit()
    response = client.get("/api/tags", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == []

def test_get_tags_success_with_tags(client, auth_headers, sample_tags_data):
    response = client.get("/api/tags", headers=auth_headers)
    json_response = response.get_json()
    assert response.status_code == 200
    assert isinstance(json_response, list)
    names = sorted([t['name'] for t in json_response])
    expected_names = sorted(["budget", "competitive", "testing"])
    assert all(name in names for name in expected_names)

def test_get_tags_unauthenticated(client):
    response = client.get("/api/tags")
    assert response.status_code == 401

def test_create_tag_success(client, app, db, auth_headers, test_user):
    payload = {"name": " New Fun Tag "}
    response = client.post("/api/tags", json=payload, headers=auth_headers)
    json_response = response.get_json()

    assert response.status_code == 201
    assert json_response["name"] == "new fun tag"
    assert "id" in json_response

    with app.app_context():
        tag = _db.session.query(Tag).filter_by(id=json_response["id"]).first()
        assert tag is not None
        assert tag.name == "new fun tag"
        assert tag.user_id == test_user.id

def test_create_tag_duplicate(client, auth_headers, sample_tags_data):
    payload = {"name": "BuDgEt"}
    response = client.post("/api/tags", json=payload, headers=auth_headers)
    assert response.status_code == 409
    assert "Tag already exists" in response.get_json().get("error", "")

def test_create_tag_missing_name(client, auth_headers):
    payload = {}
    response = client.post("/api/tags", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Missing 'name'" in response.get_json().get("error", "")

def test_create_tag_empty_name(client, auth_headers):
    payload = {"name": "   "}
    response = client.post("/api/tags", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "must be a non-empty string" in response.get_json().get("error", "")

def test_create_tag_unauthenticated(client):
    payload = {"name": "Auth Test"}
    response = client.post("/api/tags", json=payload)
    assert response.status_code == 401

def test_add_tag_to_deck_success(client, app, db, auth_headers, sample_deck_data, sample_tags_data, test_user):
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget"]
    payload = {"tag_id": tag_id}
    user_id = test_user.id

    with app.app_context():
        found_user_deck = _db.session.query(UserDeck).filter_by(user_id=user_id, deck_id=deck_id).first()
        found_tag = _db.session.query(Tag).filter_by(id=tag_id, user_id=user_id).first()
        assert found_user_deck is not None, "UserDeck should exist before API call"
        assert found_tag is not None, "Tag should exist before API call"

    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers=auth_headers)

    assert response.status_code == 201
    assert "Tag associated successfully" in response.get_json().get("message", "")

    with app.app_context():
        reloaded_deck = _db.session.get(Deck, deck_id)
        assert reloaded_deck is not None
        _db.session.refresh(reloaded_deck)
        tag_ids_on_deck = {tag.id for tag in reloaded_deck.tags}
        assert tag_id in tag_ids_on_deck


def test_add_tag_to_deck_already_associated(client, app, db, auth_headers, deck_with_tag_data):
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    payload = {"tag_id": tag_id}

    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert "Tag already associated" in response.get_json().get("message", "")


def test_add_tag_to_deck_deck_not_found(client, auth_headers, sample_tags_data):
    invalid_deck_id = 9999
    tag_id = sample_tags_data["budget"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{invalid_deck_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 404

def test_add_tag_to_deck_tag_not_found(client, auth_headers, sample_deck_data):
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 9999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 404


def test_add_tag_to_deck_deck_not_owned(client, auth_headers_user_2, sample_deck_data, sample_tags_data):
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers=auth_headers_user_2)
    assert response.status_code == 404


def test_add_tag_to_deck_tag_not_owned(client, app, db, auth_headers, sample_deck_data, test_user_2):
    deck_id = sample_deck_data["id"]
    with app.app_context():
        tag_user_2 = Tag.query.filter_by(user_id=test_user_2.id, name="user2tag").first()
        if not tag_user_2:
            tag_user_2 = Tag(user_id=test_user_2.id, name="user2tag")
            _db.session.add(tag_user_2)
            _db.session.commit()
        tag_id_user_2 = tag_user_2.id

    payload = {"tag_id": tag_id_user_2}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 404


def test_add_tag_to_deck_missing_tag_id(client, auth_headers, sample_deck_data):
    deck_id = sample_deck_data["id"]
    payload = {}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 400
    json_response = response.get_json()
    assert json_response is not None
    assert "Missing 'tag_id'" in json_response.get("error", "")


def test_add_tag_to_deck_unauthenticated(client, sample_deck_data, sample_tags_data):
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload)
    assert response.status_code == 401

def test_remove_tag_from_deck_success(client, app, db, auth_headers, deck_with_tag_data):
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]

    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}", headers=auth_headers)
    assert response.status_code == 204

    with app.app_context():
        reloaded_deck = _db.session.get(Deck, deck_id)
        assert reloaded_deck is not None
        _db.session.refresh(reloaded_deck)
        tag_ids_on_deck = {tag.id for tag in reloaded_deck.tags}
        assert tag_id not in tag_ids_on_deck

def test_remove_tag_from_deck_not_associated(client, auth_headers, deck_with_tag_data, sample_tags_data):
    deck_id = deck_with_tag_data["deck_id"]
    tag_id_not_associated = sample_tags_data["budget"]

    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id_not_associated}", headers=auth_headers)
    assert response.status_code == 404
    json_response = response.get_json()
    if json_response:
        assert "Tag is not associated" in json_response.get("error", "")

def test_remove_tag_from_deck_deck_not_found(client, auth_headers, sample_tags_data):
    invalid_deck_id = 9999
    tag_id = sample_tags_data["competitive"]
    response = client.delete(f"/api/decks/{invalid_deck_id}/tags/{tag_id}", headers=auth_headers)
    assert response.status_code == 404

def test_remove_tag_from_deck_tag_not_found(client, auth_headers, sample_deck_data):
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 9999
    response = client.delete(f"/api/decks/{deck_id}/tags/{invalid_tag_id}", headers=auth_headers)
    assert response.status_code == 404


def test_remove_tag_from_deck_deck_not_owned(client, auth_headers_user_2, deck_with_tag_data):
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}", headers=auth_headers_user_2)
    assert response.status_code == 404


def test_remove_tag_from_deck_unauthenticated(client, deck_with_tag_data):
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}")
    assert response.status_code == 401