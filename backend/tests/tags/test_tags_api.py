import pytest
from flask_bcrypt import Bcrypt
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from backend import db as _db
from backend.models import User, Tag, Deck, UserDeck, DeckType

@pytest.fixture(scope='function')
def test_user(app, db):
    bcrypt = Bcrypt(app)
    username = "tags_testuser_session"
    password = "password123"
    with app.app_context():
        stmt = select(User).where(User.username == username)
        user = _db.session.scalar(stmt)
        if not user:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(username=username, hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def test_user_2(app, db):
    bcrypt = Bcrypt(app)
    username = "tags_testuser_2_session"
    password = "password456"
    with app.app_context():
        stmt = select(User).where(User.username == username)
        user = _db.session.scalar(stmt)
        if not user:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(username=username, hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    login_resp = client.post('/api/auth/login', json={
        'username': test_user["user_obj"].username,
        'password': test_user["password"]
    })
    assert login_resp.status_code == 200
    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200
    csrf_token = csrf_resp.get_json()['csrf_token']
    assert csrf_token is not None
    yield client, csrf_token


@pytest.fixture(scope='function')
def logged_in_client_user_2(client, test_user_2):
    login_resp = client.post('/api/auth/login', json={
        'username': test_user_2["user_obj"].username,
        'password': test_user_2["password"]
    })
    assert login_resp.status_code == 200
    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200
    csrf_token = csrf_resp.get_json()['csrf_token']
    assert csrf_token is not None
    yield client, csrf_token


@pytest.fixture(scope='function')
def sample_tags_data(app, test_user):
    user_id = test_user["user_obj"].id
    with app.app_context():
        tags = {}
        tag_names = ["competitive_tags_s", "budget_tags_s", "testing_tags_s"]
        for name in tag_names:
             stmt = select(Tag).where(Tag.user_id == user_id, Tag.name == name)
             tag = _db.session.scalars(stmt).first()
             if not tag:
                  tag = Tag(user_id=user_id, name=name)
                  _db.session.add(tag)
             tags[name] = tag
        _db.session.commit()
        yield {key: tag.id for key, tag in tags.items()}


@pytest.fixture(scope='function')
def sample_deck_data(app, test_user):
    user_id = test_user["user_obj"].id
    deck_name = "Tag Test Deck Tags Sesh"
    with app.app_context():
        stmt_deck = select(Deck).where(Deck.name == deck_name, Deck.user_id == user_id)
        deck = _db.session.scalars(stmt_deck).first()
        if not deck:
            deck_type = _db.session.get(DeckType, 1)
            if not deck_type:
                deck_type = DeckType(id=1, name='Standard Tags Sesh')
                _db.session.add(deck_type)

            deck = Deck(name=deck_name, deck_type_id=deck_type.id, user_id=user_id)
            _db.session.add(deck)
            _db.session.flush()

            user_deck = UserDeck(user_id=user_id, deck_id=deck.id)
            _db.session.add(user_deck)
            _db.session.commit()
        else:
            deck = _db.session.get(Deck, deck.id, options=[selectinload(Deck.tags)])
            if deck:
                deck.tags.clear()
                _db.session.commit()

        yield {"id": deck.id, "user_id": user_id, "name": deck.name }


@pytest.fixture(scope='function')
def deck_with_tag_data(app, db, sample_deck_data, sample_tags_data):
    with app.app_context():
        deck_id = sample_deck_data["id"]
        tag_id = sample_tags_data["competitive_tags_s"]
        deck = _db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
        tag = _db.session.get(Tag, tag_id)

        if deck and tag:
            if tag not in deck.tags:
                deck.tags.append(tag)
                _db.session.commit()
        elif not deck:
             pytest.fail(f"Deck with ID {deck_id} not found in deck_with_tag_data fixture")
        elif not tag:
             pytest.fail(f"Tag with ID {tag_id} not found in deck_with_tag_data fixture")

        yield {"deck_id": deck_id, "tag_id": tag_id}


def test_get_tags_success_no_tags(app, db, logged_in_client, test_user):
    client, _ = logged_in_client
    user_id = test_user["user_obj"].id
    with app.app_context():
        stmt = delete(Tag).where(Tag.user_id == user_id)
        _db.session.execute(stmt)
        _db.session.commit()

    response = client.get("/api/tags")
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_tags_success_with_tags(logged_in_client, sample_tags_data):
    client, _ = logged_in_client
    response = client.get("/api/tags")
    json_response = response.get_json()
    assert response.status_code == 200
    assert isinstance(json_response, list)
    names_in_response = {t['name'] for t in json_response}
    expected_names = {"competitive_tags_s", "budget_tags_s", "testing_tags_s"}
    assert expected_names.issubset(names_in_response)


def test_get_tags_unauthenticated(client):
    with client.session_transaction() as sess:
        sess.clear()

    response = client.get("/api/tags")
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]


def test_create_tag_success(app, db, logged_in_client, test_user):
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    payload = {"name": " New Fun Tag Session "}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 201
    assert json_response["name"] == "new fun tag session"
    assert "id" in json_response

    with app.app_context():
        tag = _db.session.get(Tag, json_response["id"])
        assert tag is not None
        assert tag.name == "new fun tag session"
        assert tag.user_id == user_id


def test_create_tag_duplicate(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    payload = {"name": " BuDgEt_TaGs_S "}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 409
    assert "Tag already exists" in response.get_json().get("error", "")


def test_create_tag_missing_name(logged_in_client):
    client, csrf_token = logged_in_client
    payload = {}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    assert "Missing 'name'" in response.get_json().get("error", "")


def test_create_tag_empty_name(logged_in_client):
    client, csrf_token = logged_in_client
    payload = {"name": "   "}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    assert "must be a non-empty string" in response.get_json().get("error", "")


def test_create_tag_unauthenticated(client):
    with client.session_transaction() as sess:
        sess.clear()
    payload = {"name": "Auth Test Session"}
    response = client.post("/api/tags", json=payload)
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]


def test_add_tag_to_deck_success(app, db, logged_in_client, sample_deck_data, sample_tags_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}

    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )

    assert response.status_code == 201
    assert "Tag associated successfully" in response.get_json().get("message", "")

    with app.app_context():
        reloaded_deck = _db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
        assert reloaded_deck is not None
        tag_ids_on_deck = {tag.id for tag in reloaded_deck.tags}
        assert tag_id in tag_ids_on_deck


def test_add_tag_to_deck_already_associated(logged_in_client, deck_with_tag_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    payload = {"tag_id": tag_id}

    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 200
    assert "Tag already associated" in response.get_json().get("message", "")


def test_add_tag_to_deck_deck_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_deck_id = 99999
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/decks/{invalid_deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_tag_not_found(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 99999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_deck_not_owned(logged_in_client_user_2, sample_deck_data, sample_tags_data):
    client, csrf_token = logged_in_client_user_2
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_tag_not_owned(app, db, logged_in_client, sample_deck_data, test_user_2):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]

    user_2_id = test_user_2["user_obj"].id
    tag_name_user_2 = "user2tag_owned_s"
    with app.app_context():
        stmt = select(Tag).where(Tag.user_id == user_2_id, Tag.name == tag_name_user_2)
        tag_user_2 = _db.session.scalars(stmt).first()
        if not tag_user_2:
            tag_user_2 = Tag(user_id=user_2_id, name=tag_name_user_2)
            _db.session.add(tag_user_2)
            _db.session.commit()
            _db.session.refresh(tag_user_2)
        tag_id_user_2 = tag_user_2.id

    payload = {"tag_id": tag_id_user_2}
    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_missing_tag_id(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    payload = {}
    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    json_response = response.get_json()
    assert json_response is not None
    assert "Missing 'tag_id'" in json_response.get("error", "")


def test_add_tag_to_deck_unauthenticated(client, sample_deck_data, sample_tags_data):
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload)
    assert response.status_code == 401


def test_remove_tag_from_deck_success(app, db, logged_in_client, deck_with_tag_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(
        f"/api/decks/{deck_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 204

    with app.app_context():
        reloaded_deck = _db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
        assert reloaded_deck is not None
        tag_ids_on_deck = {tag.id for tag in reloaded_deck.tags}
        assert tag_id not in tag_ids_on_deck


def test_remove_tag_from_deck_not_associated(logged_in_client, deck_with_tag_data, sample_tags_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id_not_associated = sample_tags_data["budget_tags_s"]

    response = client.delete(
        f"/api/decks/{deck_id}/tags/{tag_id_not_associated}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404
    json_response = response.get_json()
    if json_response:
        assert "Tag is not associated" in json_response.get("error", "")


def test_remove_tag_from_deck_deck_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_deck_id = 99999
    tag_id = sample_tags_data["competitive_tags_s"]
    response = client.delete(
        f"/api/decks/{invalid_deck_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_deck_tag_not_found(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 99999
    response = client.delete(
        f"/api/decks/{deck_id}/tags/{invalid_tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_deck_deck_not_owned(logged_in_client_user_2, deck_with_tag_data):
    client, csrf_token = logged_in_client_user_2
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(
        f"/api/decks/{deck_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_deck_unauthenticated(client, deck_with_tag_data):
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}")
    assert response.status_code == 401