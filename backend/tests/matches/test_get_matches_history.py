# backend/tests/matches/test_get_matches_history.py
# (This file seems to be testing match tag associations rather than just history fetching)

import pytest
from flask_bcrypt import Bcrypt
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import logging

from backend import db # Use pytest-flask-sqlalchemy 'db'
from backend.models import User, Tag, Deck, DeckType, LoggedMatch, Commander 

bcrypt = Bcrypt()
logger = logging.getLogger(__name__)
COMMANDER_DECK_TYPE_ID = 7 # Global for tests

# --- Fixtures ---
# Assuming test_user and test_user_2 are defined in conftest.py or similar
# If not, you'd need to define them here or ensure they are correctly scoped.
# For this example, I'll create specific user fixtures for this test module.

@pytest.fixture(scope='function')
def test_user_m_tags(app, db): # User for match tag tests
    email = "match_tags_user1_v4@example.com"
    username = "match_tags_user1_v4"
    password = "password_mt_v4_1"
    user = db.session.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            first_name="MatchTag", last_name="UserOne", email=email, username=username,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
    elif not bcrypt.check_password_hash(user.password_hash, password):
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
    yield {"user_obj": user, "password": password}

@pytest.fixture(scope='function')
def test_user_2_m_tags(app, db): # Second user for ownership tests
    email = "match_tags_user2_v4@example.com"
    username = "match_tags_user2_v4"
    password = "password_mt_v4_2"
    user = db.session.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            first_name="MatchTag", last_name="UserTwo", email=email, username=username,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
    elif not bcrypt.check_password_hash(user.password_hash, password):
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
    yield {"user_obj": user, "password": password}

@pytest.fixture(scope='function')
def logged_in_client_m_tags(client, test_user_m_tags): # Client for user 1
    client.post('/api/auth/login', json={'email': test_user_m_tags["user_obj"].email, 'password': test_user_m_tags["password"]})
    csrf_resp = client.get('/api/auth/csrf_token')
    csrf_token = csrf_resp.get_json()['csrf_token']
    yield client, csrf_token

@pytest.fixture(scope='function')
def logged_in_client_user_2_m_tags(client, test_user_2_m_tags): # Client for user 2
    # Note: client fixture is function-scoped, so it's "fresh" for this login
    # If it wasn't, you'd need to logout user 1 first or use a different client instance.
    # For simplicity, assuming client fixture handles this or tests are isolated enough.
    client.post('/api/auth/logout') # Ensure clean session for user 2
    client.post('/api/auth/login', json={'email': test_user_2_m_tags["user_obj"].email, 'password': test_user_2_m_tags["password"]})
    csrf_resp = client.get('/api/auth/csrf_token')
    csrf_token = csrf_resp.get_json()['csrf_token']
    yield client, csrf_token


@pytest.fixture(scope='function')
def sample_tags_data_m_tags(app, db, test_user_m_tags): # Specific to this module
    user_id = test_user_m_tags["user_obj"].id
    with app.app_context():
        tags_dict = {}
        # Using the exact keys that tests will use
        tag_names_and_keys = { 
            "mt_api_comp": "Match Tag API Comp v4", 
            "mt_api_budget": "Match Tag API Budget v4", 
            "mt_api_test": "Match Tag API Test v4"
        }
        needs_commit = False
        for key, name in tag_names_and_keys.items():
             tag = db.session.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == name))
             if not tag:
                  tag = Tag(user_id=user_id, name=name)
                  db.session.add(tag)
                  needs_commit = True
             tags_dict[key] = tag # Store using the key the tests expect

        if needs_commit:
            try: db.session.commit()
            except Exception as e: db.session.rollback(); pytest.fail(f"Failed to commit sample tags: {e}")

        tag_ids = {}
        for key, tag_obj in tags_dict.items():
             if tag_obj.id is None: db.session.refresh(tag_obj)
             if tag_obj.id is None: pytest.fail(f"Tag '{key}' failed to get ID.")
             tag_ids[key] = tag_obj.id
        yield tag_ids


@pytest.fixture(scope='function')
def sample_deck_data_for_match_m_tags(app, db, test_user_m_tags): # Specific to this module
    user_id = test_user_m_tags["user_obj"].id
    deck_name = "Match Tag API Test Deck V4"
    
    with app.app_context():
        deck_type = db.session.get(DeckType, COMMANDER_DECK_TYPE_ID)
        if not deck_type:
            deck_type = DeckType(id=COMMANDER_DECK_TYPE_ID, name="Commander")
            db.session.merge(deck_type); db.session.commit(); db.session.refresh(deck_type)

        deck = db.session.scalar(select(Deck).where(Deck.name == deck_name, Deck.user_id == user_id))
        if not deck:
            deck = Deck(name=deck_name, deck_type_id=COMMANDER_DECK_TYPE_ID, user_id=user_id)
            db.session.add(deck)
            try: db.session.commit(); db.session.refresh(deck)
            except Exception as e: db.session.rollback(); pytest.fail(f"Failed to commit sample deck: {e}")
        
        if deck.id is None: pytest.fail(f"Deck '{deck_name}' failed to get ID.")
        yield {"id": deck.id, "user_id": user_id}


@pytest.fixture(scope='function')
def sample_logged_match_data_m_tags(app, db, test_user_m_tags, sample_deck_data_for_match_m_tags): # Specific
    user_id = test_user_m_tags["user_obj"].id
    deck_id = sample_deck_data_for_match_m_tags["id"]
    with app.app_context():
        match = LoggedMatch(
            logger_user_id=user_id,
            deck_id=deck_id,
            result=0, 
            player_position=1,  # Provide a default valid player_position
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(match)
        try:
            db.session.commit()
            db.session.refresh(match) 
        except Exception as e:
             db.session.rollback()
             logger.error(f"Error committing LoggedMatch in fixture: {e}")
             pytest.fail(f"Failed to commit sample LoggedMatch. Error: {e}")

        if match.id is None: pytest.fail("Failed to get LoggedMatch ID.")
        yield {"id": match.id, "user_id": user_id}


@pytest.fixture(scope='function')
def logged_match_with_tag_data_m_tags(app, db, sample_logged_match_data_m_tags, sample_tags_data_m_tags): # Specific
    with app.app_context():
        match_id = sample_logged_match_data_m_tags["id"]
        tag_id = sample_tags_data_m_tags["mt_api_comp"] # Use the correct key
        
        match = db.session.get(LoggedMatch, match_id, options=[selectinload(LoggedMatch.tags)])
        tag = db.session.get(Tag, tag_id)

        if not match: pytest.fail(f"LoggedMatch with id {match_id} not found.")
        if not tag: pytest.fail(f"Tag with id {tag_id} not found.")

        if tag not in match.tags:
             match.tags.append(tag)
             try: db.session.commit()
             except Exception as e: db.session.rollback(); pytest.fail(f"Failed to commit tag association: {e}")
        yield {"match_id": match_id, "tag_id": tag_id}


# --- Test Cases: Add Tag ---

def test_add_tag_to_match_success(app, db, logged_in_client_m_tags, sample_logged_match_data_m_tags, sample_tags_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = sample_logged_match_data_m_tags["id"]
    tag_id = sample_tags_data_m_tags["mt_api_budget"] # Use correct key
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 201 
    assert "Tag associated successfully" in response.get_json().get("message", "")
    with app.app_context():
        reloaded_match = db.session.get(LoggedMatch, match_id, options=[selectinload(LoggedMatch.tags)])
        assert reloaded_match is not None
        assert tag_id in {tag.id for tag in reloaded_match.tags}

def test_add_tag_to_match_already_associated(logged_in_client_m_tags, logged_match_with_tag_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = logged_match_with_tag_data_m_tags["match_id"]
    tag_id = logged_match_with_tag_data_m_tags["tag_id"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 200
    assert "Tag already associated" in response.get_json().get("message", "")

def test_add_tag_to_match_match_not_found(logged_in_client_m_tags, sample_tags_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    invalid_match_id = 999999
    tag_id = sample_tags_data_m_tags["mt_api_budget"] # Use correct key
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{invalid_match_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404

def test_add_tag_to_match_tag_not_found(logged_in_client_m_tags, sample_logged_match_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = sample_logged_match_data_m_tags["id"]
    invalid_tag_id = 999999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404

def test_add_tag_to_match_match_not_owned(logged_in_client_user_2_m_tags, sample_logged_match_data_m_tags, sample_tags_data_m_tags):
    client, csrf_token = logged_in_client_user_2_m_tags
    match_id = sample_logged_match_data_m_tags["id"] 
    # Use a tag owned by user 1 (test_user_m_tags) for this test to ensure the 404 is due to match ownership
    tag_id_user1 = sample_tags_data_m_tags["mt_api_budget"]
    payload = {"tag_id": tag_id_user1}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404

def test_add_tag_to_match_tag_not_owned(app, db, logged_in_client_m_tags, sample_logged_match_data_m_tags, test_user_2_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = sample_logged_match_data_m_tags["id"]
    user_2_id = test_user_2_m_tags["user_obj"].id
    tag_name_user_2 = "user2_matchtag_owned_v4" 
    with app.app_context():
        tag_user_2 = db.session.scalar(select(Tag).where(Tag.user_id == user_2_id, Tag.name == tag_name_user_2))
        if not tag_user_2:
            tag_user_2 = Tag(user_id=user_2_id, name=tag_name_user_2)
            db.session.add(tag_user_2)
            try: db.session.commit(); db.session.refresh(tag_user_2)
            except Exception as e: db.session.rollback(); pytest.fail(f"Failed to create tag for user 2: {e}")
        if tag_user_2.id is None: pytest.fail("Failed to get ID for user 2 tag.")
        tag_id_user_2 = tag_user_2.id

    payload = {"tag_id": tag_id_user_2}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404

def test_add_tag_to_match_missing_tag_id(logged_in_client_m_tags, sample_logged_match_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = sample_logged_match_data_m_tags["id"]
    payload = {} 
    response = client.post(f"/api/matches/{match_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 400
    json_response = response.get_json()
    assert "Missing 'tag_id'" in json_response.get("error", "")

def test_add_tag_to_match_unauthenticated(client, sample_logged_match_data_m_tags, sample_tags_data_m_tags):
    with client.session_transaction() as sess: sess.clear()
    match_id = sample_logged_match_data_m_tags["id"]
    tag_id = sample_tags_data_m_tags["mt_api_budget"] # Use correct key
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload)
    assert response.status_code == 401


# --- Test Cases: Remove Tag ---

def test_remove_tag_from_match_success(app, db, logged_in_client_m_tags, logged_match_with_tag_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = logged_match_with_tag_data_m_tags["match_id"]
    tag_id = logged_match_with_tag_data_m_tags["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 204
    with app.app_context():
        reloaded_match = db.session.get(LoggedMatch, match_id, options=[selectinload(LoggedMatch.tags)])
        assert reloaded_match is not None
        assert tag_id not in {tag.id for tag in reloaded_match.tags}

def test_remove_tag_from_match_not_associated(logged_in_client_m_tags, logged_match_with_tag_data_m_tags, sample_tags_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = logged_match_with_tag_data_m_tags["match_id"] 
    tag_id_not_associated = sample_tags_data_m_tags["mt_api_budget"] 
    assert logged_match_with_tag_data_m_tags["tag_id"] != tag_id_not_associated 

    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id_not_associated}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404 
    json_response = response.get_json()
    if json_response: assert "Tag is not associated" in json_response.get("error", "")

def test_remove_tag_from_match_match_not_found(logged_in_client_m_tags, sample_tags_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    invalid_match_id = 999999
    tag_id = sample_tags_data_m_tags["mt_api_comp"] # Use correct key
    response = client.delete(f"/api/matches/{invalid_match_id}/tags/{tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404

def test_remove_tag_from_match_tag_not_found(logged_in_client_m_tags, sample_logged_match_data_m_tags):
    client, csrf_token = logged_in_client_m_tags
    match_id = sample_logged_match_data_m_tags["id"]
    invalid_tag_id = 999999
    response = client.delete(f"/api/matches/{match_id}/tags/{invalid_tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404

def test_remove_tag_from_match_match_not_owned(logged_in_client_user_2_m_tags, logged_match_with_tag_data_m_tags):
    client, csrf_token = logged_in_client_user_2_m_tags
    match_id = logged_match_with_tag_data_m_tags["match_id"]
    tag_id = logged_match_with_tag_data_m_tags["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404

def test_remove_tag_from_match_unauthenticated(client, logged_match_with_tag_data_m_tags):
    with client.session_transaction() as sess: sess.clear()
    match_id = logged_match_with_tag_data_m_tags["match_id"]
    tag_id = logged_match_with_tag_data_m_tags["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}")
    assert response.status_code == 401