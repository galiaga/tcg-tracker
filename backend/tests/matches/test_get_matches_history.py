# backend/tests/matches/test_get_matches_history.py

# --- Imports ---
import pytest
from flask_bcrypt import Bcrypt
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend import db as _db
from backend.models import User, Tag, Deck, UserDeck, DeckType, Match

# --- Fixtures ---

bcrypt = Bcrypt() # Initialize Bcrypt globally for fixtures

@pytest.fixture(scope='function')
def test_user(app, db):
    """Creates or retrieves the primary test user."""
    email = "match_tags_testuser@example.com" # Use email
    first_name = "MatchTag"
    last_name = "User1"
    username = "match_tags_testuser_session" # Keep for fallback/completeness
    password = "password123"
    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user: user = _db.session.scalar(select(User).where(User.username == username)) # Fallback

        if not user:
            print(f"\nDEBUG: Creating user for match_tags tests: {email}")
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email.lower(),
                username=username,
                password_hash=hashed_password
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        else:
            print(f"\nDEBUG: Found existing user for match_tags tests: {user.email}")
            needs_update = False
            if not user.first_name: user.first_name = first_name; needs_update = True
            if not user.last_name: user.last_name = last_name; needs_update = True
            if not bcrypt.check_password_hash(user.password_hash, password):
                 print(f"\nWARN: Updating password for existing test user {user.email}")
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 needs_update = True
            if needs_update:
                 _db.session.commit()
                 _db.session.refresh(user)

        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def test_user_2(app, db):
    """Creates or retrieves the secondary test user."""
    email = "match_tags_testuser_2@example.com" # Use email
    first_name = "MatchTag"
    last_name = "User2"
    username = "match_tags_testuser_2_session" # Keep for fallback/completeness
    password = "password456"
    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user: user = _db.session.scalar(select(User).where(User.username == username)) # Fallback

        if not user:
            print(f"\nDEBUG: Creating user 2 for match_tags tests: {email}")
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email.lower(),
                username=username,
                password_hash=hashed_password
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        else:
            print(f"\nDEBUG: Found existing user 2 for match_tags tests: {user.email}")
            needs_update = False
            if not user.first_name: user.first_name = first_name; needs_update = True
            if not user.last_name: user.last_name = last_name; needs_update = True
            if not bcrypt.check_password_hash(user.password_hash, password):
                 print(f"\nWARN: Updating password for existing test user 2 {user.email}")
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 needs_update = True
            if needs_update:
                 _db.session.commit()
                 _db.session.refresh(user)

        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    """Logs in the primary test user."""
    login_resp = client.post('/api/auth/login', json={
        'email': test_user["user_obj"].email, # Login via email
        'password': test_user["password"]
    })
    assert login_resp.status_code == 200, f"Login failed for user 1: {login_resp.get_data(as_text=True)}"
    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200, "CSRF token fetch failed for user 1"
    csrf_token = csrf_resp.get_json().get('csrf_token')
    assert csrf_token is not None, "CSRF token missing for user 1"
    yield client, csrf_token


@pytest.fixture(scope='function')
def logged_in_client_user_2(client, test_user_2):
    """Logs in the secondary test user."""
    login_resp = client.post('/api/auth/login', json={
        'email': test_user_2["user_obj"].email, # Login via email
        'password': test_user_2["password"]
    })
    assert login_resp.status_code == 200, f"Login failed for user 2: {login_resp.get_data(as_text=True)}"
    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200, "CSRF token fetch failed for user 2"
    csrf_token = csrf_resp.get_json().get('csrf_token')
    assert csrf_token is not None, "CSRF token missing for user 2"
    yield client, csrf_token


@pytest.fixture(scope='function')
def sample_tags_data(app, test_user):
    """Sets up sample tags for the primary test user."""
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
    """Sets up a sample deck for the primary test user."""
    user_id = test_user["user_obj"].id
    deck_name = "Match Tag Test Deck Session"
    with app.app_context():
        stmt_deck = select(Deck).where(Deck.name == deck_name, Deck.user_id == user_id)
        deck = _db.session.scalars(stmt_deck).first()
        user_deck = None

        if not deck:
            deck_type = _db.session.get(DeckType, 1) or DeckType(id=1, name='Standard Sesh')
            _db.session.merge(deck_type) # Use merge to add if not exists

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

        if not user_deck: pytest.fail("Failed to create or find UserDeck")

        yield {"id": deck.id, "user_id": user_id, "user_deck_id": user_deck.id }


@pytest.fixture(scope='function')
def sample_match_data(app, db, test_user, sample_deck_data_for_match):
    """Sets up a sample match for the primary test user's deck."""
    user_id = test_user["user_obj"].id
    with app.app_context():
        user_deck_id = sample_deck_data_for_match["user_deck_id"]
        stmt = select(Match)\
            .where(Match.user_deck_id == user_deck_id, Match.result == 0)\
            .order_by(Match.timestamp.desc())
        match = _db.session.scalars(stmt).first()

        if not match:
            match = Match(user_deck_id=user_deck_id, result=0) # Default result to 0 (Win)
            _db.session.add(match)
            _db.session.commit()
            _db.session.refresh(match)
        else:
             # Clear tags from existing match for clean test state
             match.tags.clear()
             _db.session.commit()

        yield {"id": match.id, "user_id": user_id}


@pytest.fixture(scope='function')
def match_with_tag_data(app, db, sample_match_data, sample_tags_data):
    """Ensures a specific tag is associated with the sample match."""
    with app.app_context():
        match_id = sample_match_data["id"]
        tag_id = sample_tags_data["match_comp_s"]
        match = _db.session.get(Match, match_id, options=[selectinload(Match.tags)]) # Eager load tags
        tag = _db.session.get(Tag, tag_id)

        if not match: pytest.fail(f"Match with id {match_id} not found in fixture setup.")
        if not tag: pytest.fail(f"Tag with id {tag_id} not found in fixture setup.")

        if tag not in match.tags:
             match.tags.append(tag)
             _db.session.commit()

        yield {"match_id": match_id, "tag_id": tag_id}


# --- Test Cases ---

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
    match_id = sample_match_data["id"] # Match owned by user 1
    tag_id = sample_tags_data["match_budget_s"] # Tag owned by user 1, but irrelevant here
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404 # Should fail because match isn't owned by user 2


def test_add_tag_to_match_tag_not_owned(app, db, logged_in_client, sample_match_data, test_user_2):
    client, csrf_token = logged_in_client
    match_id = sample_match_data["id"] # Match owned by user 1

    # Create a tag owned by user 2
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
    assert response.status_code == 404 # Should fail because tag isn't owned by user 1


def test_add_tag_to_match_missing_tag_id(logged_in_client, sample_match_data):
    client, csrf_token = logged_in_client
    match_id = sample_match_data["id"]
    payload = {} # Missing tag_id
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
    tag_id_not_associated = sample_tags_data["match_budget_s"] # A tag not added in match_with_tag_data

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
    match_id = match_with_tag_data["match_id"] # Match owned by user 1
    tag_id = match_with_tag_data["tag_id"] # Tag owned by user 1
    response = client.delete(
        f"/api/matches/{match_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404 # Should fail because match isn't owned by user 2


def test_remove_tag_from_match_unauthenticated(client, match_with_tag_data):
    match_id = match_with_tag_data["match_id"]
    tag_id = match_with_tag_data["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}")
    assert response.status_code == 401