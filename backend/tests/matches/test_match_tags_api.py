import pytest
from flask_bcrypt import Bcrypt
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend import db as _db
from backend.models import User, Tag, Deck, UserDeck, DeckType, Match


@pytest.fixture(scope='function')
def test_user(app, db):
    bcrypt = Bcrypt(app)
    username = "match_tags_testuser_session"
    password = "password123"
    with app.app_context():
        stmt = select(User).where(User.username == username)
        user = _db.session.scalar(stmt)
        if not user:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(username=username, password_hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def test_user_2(app, db):
    bcrypt = Bcrypt(app)
    username = "match_tags_testuser_2_session"
    password = "password456"
    with app.app_context():
        stmt = select(User).where(User.username == username)
        user = _db.session.scalar(stmt)
        if not user:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(username=username, password_hash=hashed_password)
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
        tag_names = ["match_comp_s", "match_budget_s", "match_test_s", "user2matchtag_s"]
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
def sample_deck_data_for_match(app, test_user):
    user_id = test_user["user_obj"].id
    deck_name = "Match Tag Test Deck Session"
    with app.app_context():
        stmt_deck = select(Deck).where(Deck.name == deck_name, Deck.user_id == user_id)
        deck = _db.session.scalars(stmt_deck).first()
        user_deck = None

        if not deck:
            deck_type = _db.session.get(DeckType, 1)
            if not deck_type:
                deck_type = DeckType(id=1, name='Standard Sesh')
                _db.session.add(deck_type)

            deck = Deck(name=deck_name, deck_type_id=deck_type.id, user_id=user_id)
            _db.session.add(deck)
            _db.session.flush()

            user_deck = UserDeck(user_id=user_id, deck_id=deck.id)
            _db.session.add(user_deck)
            _db.session.commit()
        else:
            stmt_ud = select(UserDeck).where(UserDeck.user_id == user_id, UserDeck.deck_id == deck.id)
            user_deck = _db.session.scalars(stmt_ud).first()
            if not user_deck:
                 user_deck = UserDeck(user_id=user_id, deck_id=deck.id)
                 _db.session.add(user_deck)
                 _db.session.commit()

        if not user_deck:
             pytest.fail("Failed to create or find UserDeck")

        yield {"id": deck.id, "user_id": user_id, "user_deck_id": user_deck.id }


@pytest.fixture(scope='function')
def sample_match_data(app, db, test_user, sample_deck_data_for_match):
    user_id = test_user["user_obj"].id
    with app.app_context():
        user_deck_id = sample_deck_data_for_match["user_deck_id"]
        stmt = select(Match)\
            .where(Match.user_deck_id == user_deck_id, Match.result == 0)\
            .order_by(Match.timestamp.desc())
        match = _db.session.scalars(stmt).first()

        if not match:
            match = Match(user_deck_id=user_deck_id, result=0)
            _db.session.add(match)
            _db.session.commit()
            _db.session.refresh(match)
        else:
             match.tags.clear()
             _db.session.commit()

        yield {"id": match.id, "user_id": user_id}


@pytest.fixture(scope='function')
def match_with_tag_data(app, db, sample_match_data, sample_tags_data):
    with app.app_context():
        match_id = sample_match_data["id"]
        tag_id = sample_tags_data["match_comp_s"]
        match = _db.session.get(Match, match_id)
        tag = _db.session.get(Tag, tag_id)

        if match and tag:
            _db.session.refresh(match)
            if tag not in match.tags:
                 match.tags.append(tag)
                 _db.session.commit()
        elif not match:
            pytest.fail(f"Match with id {match_id} not found in fixture setup.")
        elif not tag:
             pytest.fail(f"Tag with id {tag_id} not found in fixture setup.")

        yield {"match_id": match_id, "tag_id": tag_id}


def test_add_tag_to_match_success(app, db, logged_in_client, sample_match_data, sample_tags_data):
    client, csrf_token = logged_in_client
    match_id = sample_match_data["id"]
    tag_id = sample_tags_data["match_budget_s"]
    payload = {"tag_id": tag_id}

    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 201
    assert "Tag associated successfully" in response.get_json().get("message", "")

    with app.app_context():
        reloaded_match = _db.session.get(Match, match_id, options=[selectinload(Match.tags)])
        assert reloaded_match is not None
        tag_ids_on_match = {tag.id for tag in reloaded_match.tags}
        assert tag_id in tag_ids_on_match


def test_add_tag_to_match_already_associated(logged_in_client, match_with_tag_data):
    client, csrf_token = logged_in_client
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]
    payload = {"tag_id": tag_id}

    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 200
    assert "Tag already associated" in response.get_json().get("message", "")


def test_add_tag_to_match_match_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_match_id = 99999
    tag_id = sample_tags_data["match_budget_s"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/matches/{invalid_match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_tag_not_found(logged_in_client, sample_match_data):
    client, csrf_token = logged_in_client
    match_id = sample_match_data["id"]
    invalid_tag_id = 99999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_match_not_owned(logged_in_client_user_2, sample_match_data, sample_tags_data):
    client, csrf_token = logged_in_client_user_2
    match_id = sample_match_data["id"]
    tag_id = sample_tags_data["match_budget_s"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_tag_not_owned(app, db, logged_in_client, sample_match_data, test_user_2):
    client, csrf_token = logged_in_client
    match_id = sample_match_data["id"]
    user_2_id = test_user_2["user_obj"].id
    tag_name_user_2 = "user2_matchtag_owned_s"
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
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_missing_tag_id(logged_in_client, sample_match_data):
    client, csrf_token = logged_in_client
    match_id = sample_match_data["id"]
    payload = {}
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    json_response = response.get_json()
    assert json_response is not None
    assert "Missing 'tag_id'" in json_response.get("error", "")


def test_add_tag_to_match_unauthenticated(client, sample_match_data, sample_tags_data):
    match_id = sample_match_data["id"]
    tag_id = sample_tags_data["match_budget_s"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload)
    assert response.status_code == 401


def test_remove_tag_from_match_success(app, db, logged_in_client, match_with_tag_data):
    client, csrf_token = logged_in_client
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]

    response = client.delete(
        f"/api/matches/{match_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 204

    with app.app_context():
        reloaded_match = _db.session.get(Match, match_id, options=[selectinload(Match.tags)])
        assert reloaded_match is not None
        tag_ids_on_match = {tag.id for tag in reloaded_match.tags}
        assert tag_id not in tag_ids_on_match


def test_remove_tag_from_match_not_associated(logged_in_client, match_with_tag_data, sample_tags_data):
    client, csrf_token = logged_in_client
    match_id = match_with_tag_data["match_id"]
    tag_id_not_associated = sample_tags_data["match_budget_s"]

    response = client.delete(
        f"/api/matches/{match_id}/tags/{tag_id_not_associated}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404
    json_response = response.get_json()
    if json_response:
        assert "Tag is not associated" in json_response.get("error", "")


def test_remove_tag_from_match_match_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_match_id = 99999
    tag_id = sample_tags_data["match_comp_s"]
    response = client.delete(
        f"/api/matches/{invalid_match_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_match_tag_not_found(logged_in_client, sample_match_data):
    client, csrf_token = logged_in_client
    match_id = sample_match_data["id"]
    invalid_tag_id = 99999
    response = client.delete(
        f"/api/matches/{match_id}/tags/{invalid_tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_match_match_not_owned(logged_in_client_user_2, match_with_tag_data):
    client, csrf_token = logged_in_client_user_2
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]
    response = client.delete(
        f"/api/matches/{match_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_match_unauthenticated(client, match_with_tag_data):
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}")
    assert response.status_code == 401