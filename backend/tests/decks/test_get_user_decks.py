# backend/tests/decks/test_get_user_decks.py

# --- Imports ---
import pytest
from flask_bcrypt import Bcrypt
from backend.models import User, Deck, DeckType, Tag, UserDeck
from backend import db as _db
from sqlalchemy import select

# --- Fixtures ---

bcrypt = Bcrypt() # Initialize Bcrypt globally for the fixture

@pytest.fixture(scope='function')
def test_user(app):
    """Creates or retrieves a test user required for getting decks."""
    email = "get_decks_testuser@example.com" # Use email as primary identifier
    first_name = "GetDecks"
    last_name = "Tester"
    username = "get_decks_testuser_session" # Keep for potential fallback/completeness
    password = "getdeckspw"

    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user:
            user = _db.session.scalar(select(User).where(User.username == username)) # Fallback check

        if not user:
            print(f"\nDEBUG: Creating user for get_decks tests: {email}")
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
            print(f"\nDEBUG: Found existing user for get_decks tests: {user.email}")
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
def logged_in_client(client, test_user):
    """Logs in the test user and yields the authenticated client."""
    login_resp = client.post('/api/auth/login', json={
        'email': test_user["user_obj"].email, # Login via email
        'password': test_user["password"]
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.get_data(as_text=True)}"
    yield client

@pytest.fixture(scope='function')
def decks_and_tags_setup(app, test_user):
    """Sets up deck types, tags, decks, and associations for testing."""
    user_id = test_user["user_obj"].id
    with app.app_context():
        # Ensure Deck Types exist
        type1 = _db.session.scalar(select(DeckType).where(DeckType.id == 1)) or DeckType(id=1, name="Standard")
        type2 = _db.session.scalar(select(DeckType).where(DeckType.id == 7)) or DeckType(id=7, name="Commander")
        _db.session.merge(type1)
        _db.session.merge(type2)
        _db.session.commit()

        # Ensure Tags exist
        tag_names = ["budget_s", "competitive_s", "fun_s", "lonely_s"]
        tags = {}
        for name in tag_names:
            tag = _db.session.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == name))
            if not tag:
                tag = Tag(user_id=user_id, name=name)
                _db.session.add(tag)
            tags[name] = tag
        _db.session.commit()

        # Ensure Decks exist
        deck_data = {
            "A": {"name": "Deck A Sesh (Std, Budget)", "type_id": type1.id},
            "B": {"name": "Deck B Sesh (Cmdr, Budget, Comp)", "type_id": type2.id},
            "C": {"name": "Deck C Sesh (Std, Comp)", "type_id": type1.id},
            "D": {"name": "Deck D Sesh (Cmdr, Fun)", "type_id": type2.id},
            "E": {"name": "Deck E Sesh (Std, No Tags)", "type_id": type1.id},
        }
        decks = {}
        for key, data in deck_data.items():
            deck = _db.session.scalar(select(Deck).where(Deck.user_id == user_id, Deck.name == data["name"]))
            if not deck:
                deck = Deck(user_id=user_id, name=data["name"], deck_type_id=data["type_id"])
                _db.session.add(deck)
                _db.session.flush() # Get deck ID before creating UserDeck
                user_deck = UserDeck(user_id=user_id, deck_id=deck.id)
                _db.session.add(user_deck)
            decks[key] = deck
        _db.session.commit()

        # Ensure Deck-Tag associations are correct
        deck_a = decks["A"]; deck_b = decks["B"]; deck_c = decks["C"]; deck_d = decks["D"]
        tag1 = tags["budget_s"]; tag2 = tags["competitive_s"]; tag3 = tags["fun_s"]

        # Clear existing tags first to ensure clean state
        for deck in decks.values():
            deck.tags.clear()
        _db.session.flush()

        # Add desired tags
        deck_a.tags.append(tag1)
        deck_b.tags.append(tag1); deck_b.tags.append(tag2)
        deck_c.tags.append(tag2)
        deck_d.tags.append(tag3)
        _db.session.commit()

        yield {
            "decks": {key: deck.id for key, deck in decks.items()},
            "tags": {key: tag.id for key, tag in tags.items()}
        }

# --- Tests ---

def test_get_user_decks_success_no_filter(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 5
    returned_ids = {d['id'] for d in data}
    expected_ids = set(decks_and_tags_setup["decks"].values())
    assert expected_ids.issubset(returned_ids)

def test_get_user_decks_filter_commander(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks?deck_type_id=7")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["D"] in returned_ids
    assert len(returned_ids) >= 2

def test_get_user_decks_filter_standard(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks?deck_type_id=1")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids
    assert decks_and_tags_setup["decks"]["E"] in returned_ids
    assert len(returned_ids) >= 3

def test_get_user_decks_filter_all(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks?deck_type_id=all")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 5

def test_get_user_decks_filter_invalid_type(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks?deck_type_id=xyz")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 5

def test_get_user_decks_filter_one_tag_budget(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["budget_s"]
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert len(returned_ids) >= 2

def test_get_user_decks_filter_one_tag_competitive(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["competitive_s"]
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids
    assert len(returned_ids) >= 2

def test_get_user_decks_filter_one_tag_fun(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["fun_s"]
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["D"] in returned_ids
    assert len(returned_ids) >= 1

def test_get_user_decks_filter_multiple_tags(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id_1 = decks_and_tags_setup["tags"]["budget_s"]
    tag_id_2 = decks_and_tags_setup["tags"]["competitive_s"]
    response = client.get(f"/api/user_decks?tags={tag_id_1},{tag_id_2}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids
    assert len(returned_ids) >= 3

def test_get_user_decks_filter_no_match_tag(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    lonely_tag_id = decks_and_tags_setup["tags"]["lonely_s"]
    response = client.get(f"/api/user_decks?tags={lonely_tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_user_decks_filter_combined_type_and_tag(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["budget_s"]
    deck_type_id = 1
    response = client.get(f"/api/user_decks?deck_type_id={deck_type_id}&tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert len(returned_ids) >= 1

def test_get_user_decks_filter_invalid_tag_param(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks?tags=abc")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 5

def test_get_user_decks_filter_mixed_valid_invalid_tag_param(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["budget_s"]
    response = client.get(f"/api/user_decks?tags={tag_id},abc,xyz")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert len(returned_ids) >= 2

def test_get_user_decks_unauthenticated(client):
    with client.session_transaction() as sess:
        sess.clear()
    response = client.get("/api/user_decks")
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]