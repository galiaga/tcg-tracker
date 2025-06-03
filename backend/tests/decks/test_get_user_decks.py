# backend/tests/decks/test_get_user_decks.py

# --- Imports ---
import pytest
from flask_bcrypt import Bcrypt
from backend.models import User, Deck, DeckType, Tag, UserDeck # UserDeck might be implicitly handled by Deck.user_id
from backend import db as _db
from sqlalchemy import select

# --- Fixtures ---

bcrypt = Bcrypt()

@pytest.fixture(scope='function')
def test_user(app):
    email = "get_decks_testuser_v4@example.com"
    first_name = "GetDecksV4"
    last_name = "TesterV4"
    username = "get_decks_testuser_v4_session"
    password = "getdeckspwv4"

    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user:
            user = _db.session.scalar(select(User).where(User.username == username))

        if not user:
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
            needs_update = False
            if user.first_name != first_name: user.first_name = first_name; needs_update = True
            if user.last_name != last_name: user.last_name = last_name; needs_update = True
            if not bcrypt.check_password_hash(user.password_hash, password):
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 needs_update = True
            if needs_update:
                 _db.session.commit()
                 _db.session.refresh(user)
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
def decks_and_tags_setup(app, test_user):
    user_id = test_user["user_obj"].id
    with app.app_context():
        # Ensure Commander Deck Type exists (ID 7)
        commander_type_id = 7
        commander_type_name = "Commander" # Match your v4.0.0 naming
        deck_type_commander = _db.session.get(DeckType, commander_type_id)
        if not deck_type_commander:
            deck_type_commander = _db.session.scalar(select(DeckType).where(DeckType.name == commander_type_name))
            if not deck_type_commander:
                deck_type_commander = DeckType(id=commander_type_id, name=commander_type_name)
                _db.session.merge(deck_type_commander) # Use merge to handle potential pre-existing ID
            else: # if found by name, ensure ID is correct if it matters
                if deck_type_commander.id != commander_type_id:
                    # This case is tricky, for tests better to rely on one canonical way to find/create
                    print(f"WARN: Commander deck type found by name '{commander_type_name}' but with ID {deck_type_commander.id} instead of expected {commander_type_id}")
                    # Forcing ID for test consistency if it's critical, otherwise let it be.
                    # deck_type_commander.id = commander_type_id 
                    # _db.session.merge(deck_type_commander)
                    pass # Assuming name is primary for lookup if ID isn't fixed
        _db.session.commit()


        tag_names = ["budget_v4", "competitive_v4", "fun_v4", "lonely_v4"]
        tags = {}
        for name in tag_names:
            tag = _db.session.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == name))
            if not tag:
                tag = Tag(user_id=user_id, name=name)
                _db.session.add(tag)
            tags[name] = tag
        _db.session.commit()

        # All decks are now Commander type
        deck_data = {
            "A": {"name": "Deck A v4 (Cmdr, Budget)"},
            "B": {"name": "Deck B v4 (Cmdr, Budget, Comp)"},
            "C": {"name": "Deck C v4 (Cmdr, Comp)"},
            "D": {"name": "Deck D v4 (Cmdr, Fun)"},
            "E": {"name": "Deck E v4 (Cmdr, No Tags)"},
        }
        decks = {}
        for key, data in deck_data.items():
            # Check if deck exists for this user with this name
            deck = _db.session.scalar(
                select(Deck).where(Deck.user_id == user_id, Deck.name == data["name"])
            )
            if not deck:
                deck = Deck(user_id=user_id, name=data["name"], deck_type_id=deck_type_commander.id) # All are Commander
                _db.session.add(deck)
                # UserDeck is likely implicit now if Deck has user_id directly
                # If UserDeck table still exists and is used:
                # _db.session.flush()
                # user_deck = UserDeck(user_id=user_id, deck_id=deck.id)
                # _db.session.add(user_deck)
            else: # If deck exists, ensure it's commander type for test consistency
                if deck.deck_type_id != deck_type_commander.id:
                    deck.deck_type_id = deck_type_commander.id
            decks[key] = deck
        _db.session.commit()


        deck_a = decks["A"]; deck_b = decks["B"]; deck_c = decks["C"]; deck_d = decks["D"]
        tag1 = tags["budget_v4"]; tag2 = tags["competitive_v4"]; tag3 = tags["fun_v4"]

        for deck_obj in decks.values():
            if deck_obj.id: # Ensure deck has an ID
                # Efficiently clear tags: Get existing tag associations for this deck
                current_deck_tags = deck_obj.tags[:] # Create a copy to iterate over while modifying
                for t in current_deck_tags:
                    deck_obj.tags.remove(t)
        _db.session.flush() # Apply removals

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
    # All decks created in setup are for the logged-in user and are Commander type
    assert len(data) >= 5, "Should return all 5 Commander decks created for the user"
    returned_ids = {d['id'] for d in data}
    expected_ids = set(decks_and_tags_setup["decks"].values())
    assert expected_ids.issubset(returned_ids), "Not all expected deck IDs were returned"
    for deck_info in data:
        if deck_info['id'] in expected_ids: # Check only decks created by this fixture
            assert deck_info['format_name'] == "Commander" # Or your specific name for type ID 7

# --- Deck Type Filter Tests are REMOVED or REPURPOSED ---
# Since the app is Commander-only, filtering by deck_type_id is no longer a primary feature.
# If the API endpoint `/api/user_decks` still accepts `deck_type_id` but effectively ignores it
# or only returns results if `deck_type_id=7`, these tests would change.
# For now, I'm removing them as per the "Commander (EDH) Exclusivity" breaking change.
# If you need to test that *only* Commander decks are returned regardless of filter,
# that would be a different kind of test.

# def test_get_user_decks_filter_commander(logged_in_client, decks_and_tags_setup): ...
# def test_get_user_decks_filter_standard(logged_in_client, decks_and_tags_setup): ...
# def test_get_user_decks_filter_all(logged_in_client, decks_and_tags_setup): ...
# def test_get_user_decks_filter_invalid_type(logged_in_client, decks_and_tags_setup): ...

# --- Tag Filter Tests (These should still be relevant) ---

def test_get_user_decks_filter_one_tag_budget(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["budget_v4"]
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert len(returned_ids) >= 2 # Could be more if other tests add this tag

def test_get_user_decks_filter_one_tag_competitive(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["competitive_v4"]
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids
    assert len(returned_ids) >= 2

def test_get_user_decks_filter_one_tag_fun(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["fun_v4"]
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["D"] in returned_ids
    assert len(returned_ids) >= 1

def test_get_user_decks_filter_multiple_tags_or_logic(logged_in_client, decks_and_tags_setup):
    # Assuming tag filter is OR logic (deck has EITHER tag1 OR tag2)
    client = logged_in_client
    tag_id_1 = decks_and_tags_setup["tags"]["budget_v4"]
    tag_id_2 = decks_and_tags_setup["tags"]["competitive_v4"]
    response = client.get(f"/api/user_decks?tags={tag_id_1},{tag_id_2}")
    data = response.get_json()

    assert response.status_code == 200
    returned_ids = {d['id'] for d in data}
    # Deck A (budget), Deck B (budget, comp), Deck C (comp)
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids
    assert len(returned_ids) >= 3

def test_get_user_decks_filter_no_match_tag(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    lonely_tag_id = decks_and_tags_setup["tags"]["lonely_v4"]
    response = client.get(f"/api/user_decks?tags={lonely_tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 0

# This test is now less relevant if deck_type_id filter is removed or ignored.
# If it's ignored, this test becomes similar to filtering by tag only.
# If it's strictly enforced to be 7 (Commander), then this test is fine.
def test_get_user_decks_filter_combined_type_and_tag(logged_in_client, decks_and_tags_setup):
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["budget_v4"]
    # deck_type_id = 7 # Commander
    # response = client.get(f"/api/user_decks?deck_type_id={deck_type_id}&tags={tag_id}")
    # Assuming deck_type_id filter is gone, this is just filtering by tag:
    response = client.get(f"/api/user_decks?tags={tag_id}")
    data = response.get_json()

    assert response.status_code == 200
    returned_ids = {d['id'] for d in data}
    # Deck A (budget), Deck B (budget, comp) - both are Commander
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert len(returned_ids) >= 2


def test_get_user_decks_filter_invalid_tag_param_returns_all(logged_in_client, decks_and_tags_setup):
    # Assuming invalid tag IDs are ignored and all decks are returned (or an empty list if strict)
    # Current frontend behavior implies invalid tags might be ignored, leading to no filter.
    client = logged_in_client
    response = client.get("/api/user_decks?tags=abc")
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
    # This depends on backend logic: does it return all, or empty for invalid tag?
    # Assuming it ignores invalid tags and returns all user's (Commander) decks.
    assert len(data) >= 5

def test_get_user_decks_filter_mixed_valid_invalid_tag_param(logged_in_client, decks_and_tags_setup):
    # Assuming invalid tags are ignored, and only valid ones are used for filtering.
    client = logged_in_client
    tag_id = decks_and_tags_setup["tags"]["budget_v4"]
    response = client.get(f"/api/user_decks?tags={tag_id},abc,xyz")
    data = response.get_json()

    assert response.status_code == 200
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert len(returned_ids) >= 2

def test_get_user_decks_unauthenticated(client):
    # No change needed here, session clearing is fine.
    with client.session_transaction() as sess:
        sess.clear() # Ensure no session
    response = client.get("/api/user_decks")
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]