import pytest
from flask_bcrypt import Bcrypt
from backend.models import User, Deck, DeckType, Tag, UserDeck
from backend import db as _db
from sqlalchemy import select

bcrypt = Bcrypt()

@pytest.fixture(scope='function')
def test_user(app):
    username = "get_decks_testuser_session"
    password = "getdeckspw"
    with app.app_context():
        user = _db.session.scalar(select(User).where(User.username == username))
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
    yield client 


@pytest.fixture(scope='function')
def decks_and_tags_setup(app, test_user):
    user_id = test_user["user_obj"].id
    with app.app_context():
        type1 = _db.session.scalar(select(DeckType).where(DeckType.id == 1))
        if not type1:
            type1 = DeckType(id=1, name="Standard")
            _db.session.add(type1)
        type2 = _db.session.scalar(select(DeckType).where(DeckType.id == 7))
        if not type2:
            type2 = DeckType(id=7, name="Commander")
            _db.session.add(type2)
        _db.session.commit()

        tag_names = ["budget_s", "competitive_s", "fun_s", "lonely_s"] 
        tags = {}
        for name in tag_names:
            tag = _db.session.scalar(select(Tag).where(Tag.user_id == user_id).where(Tag.name == name))
            if not tag:
                tag = Tag(user_id=user_id, name=name)
                _db.session.add(tag)
            tags[name] = tag
        _db.session.commit() 

        deck_data = {
            "A": {"name": "Deck A Sesh (Std, Budget)", "type_id": type1.id},
            "B": {"name": "Deck B Sesh (Cmdr, Budget, Comp)", "type_id": type2.id},
            "C": {"name": "Deck C Sesh (Std, Comp)", "type_id": type1.id},
            "D": {"name": "Deck D Sesh (Cmdr, Fun)", "type_id": type2.id},
            "E": {"name": "Deck E Sesh (Std, No Tags)", "type_id": type1.id},
        }
        decks = {}
        for key, data in deck_data.items():
            deck = _db.session.scalar(select(Deck).where(Deck.user_id == user_id).where(Deck.name == data["name"]))
            if not deck:
                deck = Deck(user_id=user_id, name=data["name"], deck_type_id=data["type_id"])
                _db.session.add(deck)
                _db.session.flush() 
                user_deck = _db.session.scalar(select(UserDeck).where(UserDeck.user_id == user_id).where(UserDeck.deck_id == deck.id))
                if not user_deck:
                     user_deck = UserDeck(user_id=user_id, deck_id=deck.id)
                     _db.session.add(user_deck)
            decks[key] = deck
        _db.session.commit() 

        deck_a = decks["A"]
        deck_b = decks["B"]
        deck_c = decks["C"]
        deck_d = decks["D"]
        tag1 = tags["budget_s"]
        tag2 = tags["competitive_s"]
        tag3 = tags["fun_s"]

        deck_a.tags.clear()
        deck_b.tags.clear()
        deck_c.tags.clear()
        deck_d.tags.clear()
        _db.session.flush()

        deck_a.tags.append(tag1)
        deck_b.tags.append(tag1)
        deck_b.tags.append(tag2)
        deck_c.tags.append(tag2)
        deck_d.tags.append(tag3)
        _db.session.commit() 

        yield {
            "decks": {key: deck.id for key, deck in decks.items()},
            "tags": {key: tag.id for key, tag in tags.items()}
        }


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