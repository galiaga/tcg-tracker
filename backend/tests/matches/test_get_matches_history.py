import pytest
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from backend.models import User, Deck, DeckType, Tag, UserDeck, Match
from backend import db as _db
from sqlalchemy.orm import selectinload

bcrypt = Bcrypt()

@pytest.fixture(scope='function')
def test_user(app, db):
    with app.app_context():
        user = _db.session.query(User).filter_by(username="match_hist_testuser").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("matchhistpw").decode("utf-8")
            user = User(username="match_hist_testuser", hash=hashed_password)
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
def sample_tags_for_matches(app, db, test_user):
    with app.app_context():
        tags = {}
        tag_names = ["vs_aggro", "tournament", "casual"]
        for name in tag_names:
             tag = _db.session.query(Tag).filter_by(user_id=test_user.id, name=name).first()
             if not tag:
                  tag = Tag(user_id=test_user.id, name=name)
                  _db.session.add(tag)
                  _db.session.commit()
                  _db.session.refresh(tag) 
             tags[name] = tag
        yield {key: tag.id for key, tag in tags.items()} 

@pytest.fixture(scope='function')
def decks_for_matches(app, db, test_user):
    with app.app_context():
        decks_info = {}
        deck_configs = [
            {"id": 101, "name": "Match Test Deck X", "type_id": 1},
            {"id": 102, "name": "Match Test Deck Y", "type_id": 7}
        ]

        for config in deck_configs:
            deck_type = _db.session.get(DeckType, config["type_id"])
            if not deck_type:
                 deck_type = DeckType(id=config["type_id"], name=f"Type {config['type_id']}")
                 _db.session.add(deck_type)
                 _db.session.commit()

            deck = _db.session.query(Deck).filter_by(user_id=test_user.id, name=config["name"]).first()
            user_deck = None
            if not deck:
                deck = Deck(user_id=test_user.id, name=config["name"], deck_type_id=config["type_id"])
                _db.session.add(deck)
                _db.session.flush()
                user_deck = UserDeck(user_id=test_user.id, deck_id=deck.id)
                _db.session.add(user_deck)
                _db.session.commit()
            else:
                 user_deck = _db.session.query(UserDeck).filter_by(user_id=test_user.id, deck_id=deck.id).first()
                 if not user_deck:
                      user_deck = UserDeck(user_id=test_user.id, deck_id=deck.id)
                      _db.session.add(user_deck)
                      _db.session.commit()

            decks_info[config["name"]] = {"deck_id": deck.id, "user_deck_id": user_deck.id}

        yield decks_info

@pytest.fixture(scope='function')
def matches_and_tags_setup(app, db, test_user, sample_tags_for_matches, decks_for_matches):
    with app.app_context():
        user_deck_id_x = decks_for_matches["Match Test Deck X"]["user_deck_id"]
        user_deck_id_y = decks_for_matches["Match Test Deck Y"]["user_deck_id"]
        tag1_id = sample_tags_for_matches["vs_aggro"]
        tag2_id = sample_tags_for_matches["tournament"]
        tag3_id = sample_tags_for_matches["casual"]

        tag1 = _db.session.get(Tag, tag1_id)
        tag2 = _db.session.get(Tag, tag2_id)
        tag3 = _db.session.get(Tag, tag3_id)

        matches_data = [
            {"id_key": "A", "user_deck_id": user_deck_id_x, "result": 0, "tags_to_add": [tag1]},
            {"id_key": "B", "user_deck_id": user_deck_id_y, "result": 1, "tags_to_add": [tag1, tag2]},
            {"id_key": "C", "user_deck_id": user_deck_id_x, "result": 0, "tags_to_add": [tag2]},
            {"id_key": "D", "user_deck_id": user_deck_id_y, "result": 2, "tags_to_add": [tag3]},
            {"id_key": "E", "user_deck_id": user_deck_id_x, "result": 1, "tags_to_add": []},
        ]

        matches = {}
        created_matches = []
        for m_data in matches_data:
            match = Match(user_deck_id=m_data["user_deck_id"], result=m_data["result"])
            _db.session.add(match)
            created_matches.append((match, m_data["tags_to_add"], m_data["id_key"]))

        _db.session.commit() 

        for match, tags_to_add, id_key in created_matches:
            _db.session.refresh(match) 
            for tag_obj in tags_to_add:
                 tag_in_session = _db.session.merge(tag_obj)
                 if tag_in_session not in match.tags:
                      match.tags.append(tag_in_session)
            matches[id_key] = match.id

        _db.session.commit()

        yield {
            "matches": matches,
            "tags": sample_tags_for_matches,
            "decks": decks_for_matches
        }


def test_get_matches_history_no_filter(client, auth_headers, matches_and_tags_setup):
    response = client.get("/api/matches_history", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 5
    returned_ids = {m['id'] for m in data}
    expected_ids = set(matches_and_tags_setup["matches"].values())
    assert returned_ids.issuperset(expected_ids)

def test_get_matches_history_filter_tag1(client, auth_headers, matches_and_tags_setup):
    tag_id = matches_and_tags_setup["tags"]["vs_aggro"]
    response = client.get(f"/api/matches_history?tags={tag_id}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 2
    returned_ids = {m['id'] for m in data}
    assert matches_and_tags_setup["matches"]["A"] in returned_ids
    assert matches_and_tags_setup["matches"]["B"] in returned_ids

def test_get_matches_history_filter_tag2(client, auth_headers, matches_and_tags_setup):
    tag_id = matches_and_tags_setup["tags"]["tournament"]
    response = client.get(f"/api/matches_history?tags={tag_id}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 2
    returned_ids = {m['id'] for m in data}
    assert matches_and_tags_setup["matches"]["B"] in returned_ids
    assert matches_and_tags_setup["matches"]["C"] in returned_ids

def test_get_matches_history_filter_tag3(client, auth_headers, matches_and_tags_setup):
    tag_id = matches_and_tags_setup["tags"]["casual"]
    response = client.get(f"/api/matches_history?tags={tag_id}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]['id'] == matches_and_tags_setup["matches"]["D"]

def test_get_matches_history_filter_multiple_tags(client, auth_headers, matches_and_tags_setup):
    tag_id_1 = matches_and_tags_setup["tags"]["vs_aggro"]
    tag_id_2 = matches_and_tags_setup["tags"]["tournament"]
    response = client.get(f"/api/matches_history?tags={tag_id_1},{tag_id_2}", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 3 
    returned_ids = {m['id'] for m in data}
    assert matches_and_tags_setup["matches"]["A"] in returned_ids
    assert matches_and_tags_setup["matches"]["B"] in returned_ids
    assert matches_and_tags_setup["matches"]["C"] in returned_ids

def test_get_matches_history_filter_no_match_tag(client, app, db, test_user, auth_headers, matches_and_tags_setup):
     with app.app_context():
          lonely_tag = _db.session.query(Tag).filter_by(user_id=test_user.id, name="lonely_match_tag").first()
          if not lonely_tag:
              lonely_tag = Tag(user_id=test_user.id, name="lonely_match_tag")
              _db.session.add(lonely_tag)
              _db.session.commit()
          lonely_tag_id = lonely_tag.id

     response = client.get(f"/api/matches_history?tags={lonely_tag_id}", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 0
     assert data == []

def test_get_matches_history_filter_combined_deck_and_tag(client, auth_headers, matches_and_tags_setup):
     tag_id = matches_and_tags_setup["tags"]["vs_aggro"]
     deck_id = matches_and_tags_setup["decks"]["Match Test Deck X"]["deck_id"]

     response = client.get(f"/api/matches_history?deck_id={deck_id}&tags={tag_id}", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 1
     assert data[0]['id'] == matches_and_tags_setup["matches"]["A"]

def test_get_matches_history_filter_invalid_tag_param(client, auth_headers, matches_and_tags_setup):
     response = client.get("/api/matches_history?tags=abc", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) >= 5 

def test_get_matches_history_filter_mixed_valid_invalid_tag_param(client, auth_headers, matches_and_tags_setup):
     tag_id = matches_and_tags_setup["tags"]["vs_aggro"]
     response = client.get(f"/api/matches_history?tags={tag_id},abc,xyz", headers=auth_headers)
     data = response.get_json()
     assert response.status_code == 200
     assert len(data) == 2
     returned_ids = {m['id'] for m in data}
     assert matches_and_tags_setup["matches"]["A"] in returned_ids
     assert matches_and_tags_setup["matches"]["B"] in returned_ids

def test_get_matches_history_unauthenticated(client):
    response = client.get("/api/matches_history")
    assert response.status_code == 401