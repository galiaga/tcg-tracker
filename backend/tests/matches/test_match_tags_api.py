import pytest
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt

from backend.models import User, Tag, Deck, UserDeck, DeckType, Match
from backend import db as _db
from sqlalchemy.orm import selectinload

@pytest.fixture(scope='function')
def test_user(app, db):
    bcrypt = Bcrypt(app)
    with app.app_context():
        user = User.query.filter_by(username="match_tags_testuser").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("password123").decode("utf-8")
            user = User(username="match_tags_testuser", hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
        yield user

@pytest.fixture(scope='function')
def test_user_2(app, db):
    bcrypt = Bcrypt(app)
    with app.app_context():
        user = User.query.filter_by(username="match_tags_testuser_2").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("password456").decode("utf-8")
            user = User(username="match_tags_testuser_2", hash=hashed_password)
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
        tag_names = ["match_comp", "match_budget", "match_test"]
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
def sample_deck_data_for_match(app, db, test_user):
     with app.app_context():
        deck = Deck.query.filter_by(name="Match Tag Test Deck", user_id=test_user.id).first()
        if not deck:
            deck_type = DeckType.query.filter_by(id=1).first()
            if not deck_type:
                deck_type = DeckType(id=1, name='Standard')
                _db.session.add(deck_type)
                _db.session.commit()

            deck = Deck(
                name="Match Tag Test Deck",
                deck_type_id=deck_type.id,
                user_id=test_user.id
            )
            _db.session.add(deck)
            _db.session.flush()

            user_deck = UserDeck(user_id=test_user.id, deck_id=deck.id)
            _db.session.add(user_deck)
            _db.session.commit()
        else:
            user_deck = UserDeck.query.filter_by(user_id=test_user.id, deck_id=deck.id).first()
            if not user_deck:
                 user_deck = UserDeck(user_id=test_user.id, deck_id=deck.id)
                 _db.session.add(user_deck)
                 _db.session.commit()

        yield {"id": deck.id, "user_id": test_user.id, "user_deck_id": user_deck.id }

@pytest.fixture(scope='function')
def sample_match_data(app, db, test_user, sample_deck_data_for_match):
    with app.app_context():
        user_deck_id = sample_deck_data_for_match["user_deck_id"]
        # Buscar si ya existe una partida para evitar duplicados innecesarios
        match = Match.query.filter_by(user_deck_id=user_deck_id, result=0).first() # Busca una victoria como ejemplo
        if not match:
            match = Match(user_deck_id=user_deck_id, result=0) # 0 = Win
            _db.session.add(match)
            _db.session.commit()
        yield {"id": match.id, "user_id": test_user.id}


@pytest.fixture(scope='function')
def match_with_tag_data(app, db, sample_match_data, sample_tags_data):
    with app.app_context():
        match_id = sample_match_data["id"]
        tag_id = sample_tags_data["match_comp"]
        match = _db.session.get(Match, match_id)
        tag = _db.session.get(Tag, tag_id)

        if match and tag:
            _db.session.refresh(match)
            if tag not in match.tags:
                 match.tags.append(tag)
                 _db.session.commit()
        yield {"match_id": match_id, "tag_id": tag_id}


def test_add_tag_to_match_success(client, app, db, auth_headers, sample_match_data, sample_tags_data):
    match_id = sample_match_data["id"]
    tag_id = sample_tags_data["match_budget"]
    payload = {"tag_id": tag_id}

    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert "Tag associated successfully" in response.get_json().get("message", "")

    with app.app_context():
        reloaded_match = _db.session.get(Match, match_id)
        assert reloaded_match is not None
        _db.session.refresh(reloaded_match)
        tag_ids_on_match = {tag.id for tag in reloaded_match.tags}
        assert tag_id in tag_ids_on_match


def test_add_tag_to_match_already_associated(client, app, db, auth_headers, match_with_tag_data):
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]
    payload = {"tag_id": tag_id}

    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert "Tag already associated" in response.get_json().get("message", "")


def test_add_tag_to_match_match_not_found(client, auth_headers, sample_tags_data):
    invalid_match_id = 9999
    tag_id = sample_tags_data["match_budget"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{invalid_match_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 404

def test_add_tag_to_match_tag_not_found(client, auth_headers, sample_match_data):
    match_id = sample_match_data["id"]
    invalid_tag_id = 9999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 404


def test_add_tag_to_match_match_not_owned(client, auth_headers_user_2, sample_match_data, sample_tags_data):
    match_id = sample_match_data["id"]
    tag_id = sample_tags_data["match_budget"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers=auth_headers_user_2)
    assert response.status_code == 404


def test_add_tag_to_match_tag_not_owned(client, app, db, auth_headers, sample_match_data, test_user_2):
    match_id = sample_match_data["id"]
    with app.app_context():
        tag_user_2 = Tag.query.filter_by(user_id=test_user_2.id, name="user2matchtag").first()
        if not tag_user_2:
            tag_user_2 = Tag(user_id=test_user_2.id, name="user2matchtag")
            _db.session.add(tag_user_2)
            _db.session.commit()
        tag_id_user_2 = tag_user_2.id

    payload = {"tag_id": tag_id_user_2}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 404


def test_add_tag_to_match_missing_tag_id(client, auth_headers, sample_match_data):
    match_id = sample_match_data["id"]
    payload = {}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers=auth_headers)
    assert response.status_code == 400
    json_response = response.get_json()
    assert json_response is not None
    assert "Missing 'tag_id'" in json_response.get("error", "")


def test_add_tag_to_match_unauthenticated(client, sample_match_data, sample_tags_data):
    match_id = sample_match_data["id"]
    tag_id = sample_tags_data["match_budget"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload)
    assert response.status_code == 401

def test_remove_tag_from_match_success(client, app, db, auth_headers, match_with_tag_data):
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]

    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}", headers=auth_headers)
    assert response.status_code == 204

    with app.app_context():
        reloaded_match = _db.session.get(Match, match_id)
        assert reloaded_match is not None
        _db.session.refresh(reloaded_match)
        tag_ids_on_match = {tag.id for tag in reloaded_match.tags}
        assert tag_id not in tag_ids_on_match

def test_remove_tag_from_match_not_associated(client, auth_headers, match_with_tag_data, sample_tags_data):
    match_id = match_with_tag_data["match_id"]
    tag_id_not_associated = sample_tags_data["match_budget"]

    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id_not_associated}", headers=auth_headers)
    assert response.status_code == 404
    json_response = response.get_json()
    if json_response:
        assert "Tag is not associated" in json_response.get("error", "")

def test_remove_tag_from_match_match_not_found(client, auth_headers, sample_tags_data):
    invalid_match_id = 9999
    tag_id = sample_tags_data["match_comp"]
    response = client.delete(f"/api/matches/{invalid_match_id}/tags/{tag_id}", headers=auth_headers)
    assert response.status_code == 404

def test_remove_tag_from_match_tag_not_found(client, auth_headers, sample_match_data):
    match_id = sample_match_data["id"]
    invalid_tag_id = 9999
    response = client.delete(f"/api/matches/{match_id}/tags/{invalid_tag_id}", headers=auth_headers)
    assert response.status_code == 404


def test_remove_tag_from_match_match_not_owned(client, auth_headers_user_2, match_with_tag_data):
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}", headers=auth_headers_user_2)
    assert response.status_code == 404


def test_remove_tag_from_match_unauthenticated(client, match_with_tag_data):
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}")
    assert response.status_code == 401