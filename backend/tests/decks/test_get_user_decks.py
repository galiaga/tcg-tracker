import pytest
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from backend.models import User, Deck, DeckType, Tag, UserDeck
from backend import db as _db

bcrypt = Bcrypt()

@pytest.fixture(scope='function')
def test_user(app, db):
    with app.app_context():
        user = _db.session.query(User).filter_by(username="get_decks_testuser").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("getdeckspw").decode("utf-8")
            user = User(username="get_decks_testuser", hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
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
def decks_and_tags_setup(app, db, test_user):
    with app.app_context():
        type1 = _db.session.query(DeckType).filter_by(id=1).first()
        if not type1:
            type1 = DeckType(id=1, name="Standard")
            _db.session.add(type1)

        type2 = _db.session.query(DeckType).filter_by(id=7).first()
        if not type2:
            type2 = DeckType(id=7, name="Commander")
            _db.session.add(type2)

        tag_names = ["budget", "competitive", "fun"]
        tags = {}
        for name in tag_names:
            tag = _db.session.query(Tag).filter_by(user_id=test_user.id, name=name).first()
            if not tag:
                tag = Tag(user_id=test_user.id, name=name)
                _db.session.add(tag)
            tags[name] = tag

        _db.session.commit()

        deck_data = {
            "A": {"name": "Deck A (Std, Budget)", "type_id": type1.id},
            "B": {"name": "Deck B (Cmdr, Budget, Comp)", "type_id": type2.id},
            "C": {"name": "Deck C (Std, Comp)", "type_id": type1.id},
            "D": {"name": "Deck D (Cmdr, Fun)", "type_id": type2.id},
            "E": {"name": "Deck E (Std, No Tags)", "type_id": type1.id},
        }
        decks = {}
        for key, data in deck_data.items():
            deck = _db.session.query(Deck).filter_by(user_id=test_user.id, name=data["name"]).first()
            if not deck:
                deck = Deck(user_id=test_user.id, name=data["name"], deck_type_id=data["type_id"])
                _db.session.add(deck)
                _db.session.flush()
                user_deck = UserDeck(user_id=test_user.id, deck_id=deck.id)
                _db.session.add(user_deck)
            decks[key] = deck

        _db.session.commit()

        deck_a = decks["A"]
        deck_b = decks["B"]
        deck_c = decks["C"]
        deck_d = decks["D"]
        tag1 = tags["budget"]
        tag2 = tags["competitive"]
        tag3 = tags["fun"]

        if tag1 not in deck_a.tags: deck_a.tags.append(tag1)
        if tag1 not in deck_b.tags: deck_b.tags.append(tag1)
        if tag2 not in deck_b.tags: deck_b.tags.append(tag2)
        if tag2 not in deck_c.tags: deck_c.tags.append(tag2)
        if tag3 not in deck_d.tags: deck_d.tags.append(tag3)

        _db.session.commit()

        yield {
            "decks": {key: deck.id for key, deck in decks.items()},
            "tags": {key: tag.id for key, tag in tags.items()}
        }


def test_get_user_decks_success_no_filter(client, auth_headers, decks_and_tags_setup):
    response = client.get("/api/user_decks", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 5
    returned_ids = {d['id'] for d in data}
    expected_ids = set(decks_and_tags_setup["decks"].values())
    assert returned_ids == expected_ids

def test_get_user_decks_filter_commander(client, auth_headers, decks_and_tags_setup):
    response = client.get("/api/user_decks?deck_type_id=7", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 2
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["D"] in returned_ids

def test_get_user_decks_filter_standard(client, auth_headers, decks_and_tags_setup):
    response = client.get("/api/user_decks?deck_type_id=1", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 3
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids
    assert decks_and_tags_setup["decks"]["E"] in returned_ids

def test_get_user_decks_filter_all(client, auth_headers, decks_and_tags_setup):
    response = client.get("/api/user_decks?deck_type_id=all", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 5

def test_get_user_decks_filter_invalid_type(client, auth_headers, decks_and_tags_setup):
     response = client.get("/api/user_decks?deck_type_id=xyz", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 5

def test_get_user_decks_filter_one_tag_budget(client, auth_headers, decks_and_tags_setup):
    tag_id = decks_and_tags_setup["tags"]["budget"]
    response = client.get(f"/api/user_decks?tags={tag_id}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 2
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids

def test_get_user_decks_filter_one_tag_competitive(client, auth_headers, decks_and_tags_setup):
    tag_id = decks_and_tags_setup["tags"]["competitive"]
    response = client.get(f"/api/user_decks?tags={tag_id}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 2
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids

def test_get_user_decks_filter_one_tag_fun(client, auth_headers, decks_and_tags_setup):
    tag_id = decks_and_tags_setup["tags"]["fun"]
    response = client.get(f"/api/user_decks?tags={tag_id}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]['id'] == decks_and_tags_setup["decks"]["D"]

def test_get_user_decks_filter_multiple_tags(client, auth_headers, decks_and_tags_setup):
    tag_id_1 = decks_and_tags_setup["tags"]["budget"]
    tag_id_2 = decks_and_tags_setup["tags"]["competitive"]
    response = client.get(f"/api/user_decks?tags={tag_id_1},{tag_id_2}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 3
    returned_ids = {d['id'] for d in data}
    assert decks_and_tags_setup["decks"]["A"] in returned_ids
    assert decks_and_tags_setup["decks"]["B"] in returned_ids
    assert decks_and_tags_setup["decks"]["C"] in returned_ids

def test_get_user_decks_filter_no_match_tag(client, app, db, test_user, auth_headers, decks_and_tags_setup):
     with app.app_context():
          lonely_tag = _db.session.query(Tag).filter_by(user_id=test_user.id, name="lonely").first()
          if not lonely_tag:
              lonely_tag = Tag(user_id=test_user.id, name="lonely")
              _db.session.add(lonely_tag)
              _db.session.commit()
          lonely_tag_id = lonely_tag.id

     response = client.get(f"/api/user_decks?tags={lonely_tag_id}", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 0
     assert data == []

def test_get_user_decks_filter_combined_type_and_tag(client, auth_headers, decks_and_tags_setup):
     tag_id = decks_and_tags_setup["tags"]["budget"]
     deck_type_id = 1
     response = client.get(f"/api/user_decks?deck_type_id={deck_type_id}&tags={tag_id}", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 1
     assert data[0]['id'] == decks_and_tags_setup["decks"]["A"]

def test_get_user_decks_filter_invalid_tag_param(client, auth_headers, decks_and_tags_setup):
     response = client.get("/api/user_decks?tags=abc", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 5

def test_get_user_decks_filter_mixed_valid_invalid_tag_param(client, auth_headers, decks_and_tags_setup):
     tag_id = decks_and_tags_setup["tags"]["budget"]
     response = client.get(f"/api/user_decks?tags={tag_id},abc,xyz", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 2
     returned_ids = {d['id'] for d in data}
     assert decks_and_tags_setup["decks"]["A"] in returned_ids
     assert decks_and_tags_setup["decks"]["B"] in returned_ids

def test_get_user_decks_unauthenticated(client):
    response = client.get("/api/user_decks")
    assert response.status_code == 401