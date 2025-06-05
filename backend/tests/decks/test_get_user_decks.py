# backend/tests/decks/test_get_user_decks.py

import pytest
from flask_bcrypt import Bcrypt
from backend.models import User, Deck, DeckType, Tag
from backend import db # Use pytest-flask-sqlalchemy 'db'
from sqlalchemy import select

COMMANDER_DECK_TYPE_ID = 7
COMMANDER_DECK_TYPE_NAME = "Commander"

bcrypt = Bcrypt()

@pytest.fixture(scope='function')
def test_user(app, db): # Added db fixture
    email = "get_decks_testuser_v5@example.com" # Unique email
    first_name = "GetDecksV5"
    last_name = "TesterV5"
    username = "get_decks_v5_session" # Unique username
    password = "getdeckspwv5"

    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == email.lower()))
        if not user:
            user = db.session.scalar(select(User).where(User.username == username))

        if not user:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(first_name=first_name, last_name=last_name, email=email.lower(), username=username, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
        else:
            needs_update = False
            if user.first_name != first_name: user.first_name = first_name; needs_update = True
            if user.last_name != last_name: user.last_name = last_name; needs_update = True
            if not bcrypt.check_password_hash(user.password_hash, password):
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 needs_update = True
            if needs_update:
                 db.session.commit()
                 db.session.refresh(user)
        yield {"user_obj": user, "password": password}

@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    login_resp = client.post('/api/auth/login', json={
        'email': test_user["user_obj"].email,
        'password': test_user["password"]
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.get_data(as_text=True)}"
    yield client

@pytest.fixture(scope='function')
def decks_and_tags_setup(app, db, test_user): # Added db fixture
    user_id = test_user["user_obj"].id
    with app.app_context():
        deck_type_commander = db.session.get(DeckType, COMMANDER_DECK_TYPE_ID)
        if not deck_type_commander:
            deck_type_commander = DeckType(id=COMMANDER_DECK_TYPE_ID, name=COMMANDER_DECK_TYPE_NAME)
            db.session.merge(deck_type_commander)
            db.session.commit()
            db.session.refresh(deck_type_commander) # Ensure it's loaded for use

        tag_names = ["budget_v5", "competitive_v5", "fun_v5", "lonely_v5"] # Unique names
        tags = {}
        for name in tag_names:
            tag = db.session.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == name))
            if not tag:
                tag = Tag(user_id=user_id, name=name)
                db.session.add(tag)
            tags[name] = tag
        db.session.commit() # Commit tags

        deck_data = {
            "A": {"name": "Deck A v5 (Cmdr, Budget)"},
            "B": {"name": "Deck B v5 (Cmdr, Budget, Comp)"},
            "C": {"name": "Deck C v5 (Cmdr, Comp)"},
            "D": {"name": "Deck D v5 (Cmdr, Fun)"},
            "E": {"name": "Deck E v5 (Cmdr, No Tags)"},
        }
        decks = {}
        for key, data in deck_data.items():
            deck = db.session.scalar(select(Deck).where(Deck.user_id == user_id, Deck.name == data["name"]))
            if not deck:
                deck = Deck(user_id=user_id, name=data["name"], deck_type_id=COMMANDER_DECK_TYPE_ID)
                db.session.add(deck)
            elif deck.deck_type_id != COMMANDER_DECK_TYPE_ID: # Ensure existing test decks are Commander
                deck.deck_type_id = COMMANDER_DECK_TYPE_ID
                db.session.add(deck)
            decks[key] = deck
        db.session.commit() # Commit decks

        # Refresh to ensure IDs
        for deck_obj in decks.values():
            if deck_obj.id is None: db.session.refresh(deck_obj)
        for tag_obj in tags.values():
            if tag_obj.id is None: db.session.refresh(tag_obj)


        deck_a = decks["A"]; deck_b = decks["B"]; deck_c = decks["C"]; deck_d = decks["D"]
        tag1 = tags["budget_v5"]; tag2 = tags["competitive_v5"]; tag3 = tags["fun_v5"]

        # Clear existing tags before re-assigning for test idempotency
        for deck_obj in [deck_a, deck_b, deck_c, deck_d]:
            if deck_obj and deck_obj.tags: # Check if deck_obj is not None
                deck_obj.tags.clear()
        db.session.commit()


        if deck_a and tag1: deck_a.tags.append(tag1)
        if deck_b and tag1: deck_b.tags.append(tag1)
        if deck_b and tag2: deck_b.tags.append(tag2)
        if deck_c and tag2: deck_c.tags.append(tag2)
        if deck_d and tag3: deck_d.tags.append(tag3)
        db.session.commit()

        yield {
            "decks": {key: deck.id for key, deck in decks.items() if deck.id is not None},
            "tags": {key: tag.id for key, tag in tags.items() if tag.id is not None}
        }

# --- Tests ---

def test_get_user_decks_success_no_filter(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 5, "Should return at least all 5 Commander decks created for the user"
    
    returned_ids = {d['id'] for d in data}
    expected_ids = set(decks_and_tags_setup["decks"].values())
    assert expected_ids.issubset(returned_ids), "Not all expected deck IDs were returned"
    
    for deck_info in data:
        if deck_info['id'] in expected_ids: 
            assert deck_info.get('format_name') == COMMANDER_DECK_TYPE_NAME, f"Deck {deck_info['id']} missing or incorrect format_name"
            assert deck_info.get('deck_type_id') == COMMANDER_DECK_TYPE_ID

def test_get_user_decks_filter_one_tag_budget(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["budget_v5"]
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    # Check exact count if other tests don't interfere, or >=
    assert len(returned_ids) == 2 # Deck A and Deck B have budget_v5 tag

# ... (other tag filter tests: competitive, fun, multiple_tags, no_match_tag)
# Ensure they use the updated tag names (e.g., "competitive_v5") and check counts accurately.

def test_get_user_decks_filter_multiple_tags_or_logic(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id_1 = decks_and_tags_setup["tags"]["budget_v5"]
    tag_id_2 = decks_and_tags_setup["tags"]["competitive_v5"]
    response = client.get(f"/api/user_decks?tags={tag_id_1},{tag_id_2}")
    data = response.get_json()

    assert response.status_code == 200
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids # Budget
    assert decks_and_tags_setup["decks"]["B"] in returned_ids # Budget & Comp
    assert decks_and_tags_setup["decks"]["C"] in returned_ids # Comp
    assert len(returned_ids) == 3

def test_get_user_decks_filter_invalid_tag_param_returns_all_commander_decks(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    response = client.get("/api/user_decks?tags=abc") # Invalid tag ID
    data = response.get_json()
    assert response.status_code == 200 # Assuming backend ignores invalid tags and returns all (Commander) decks
    assert isinstance(data, list)
    assert len(data) >= 5 # Should be all decks for the user

def test_get_user_decks_unauthenticated(client):
    with client.session_transaction() as sess:
        sess.clear()
    response = client.get("/api/user_decks")
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]