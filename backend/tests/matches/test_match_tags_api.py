# backend/tests/tags/test_tags_api.py

import pytest
from sqlalchemy import select
from backend.models import User, Deck, Tag, DeckType # Assuming DeckType is needed for deck setup
from backend import db as _db
import logging

logger = logging.getLogger(__name__)

# NOTE: Assuming test_user, test_user_2, logged_in_client, logged_in_client_user_2
#       are correctly defined in conftest.py now.

# --- Fixtures ---

@pytest.fixture(scope="function")
def sample_tags_data(app, db, test_user):
    """Creates sample tags for the primary test user."""
    user_id = test_user["user_obj"].id
    tags = {}
    tag_names = ["competitive_tags_s", "budget_tags_s", "testing_tags_s"] # Suffix 's' for session scope hint
    with app.app_context():
        needs_commit = False
        for name in tag_names:
            stmt = select(Tag).where(Tag.user_id == user_id, Tag.name == name)
            tag = db.session.scalars(stmt).first()
            if not tag:
                tag = Tag(user_id=user_id, name=name)
                db.session.add(tag)
                needs_commit = True
            tags[name] = tag
        if needs_commit:
            try:
                db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 logger.error(f"Error committing tags in tags_api fixture: {e}")
                 pytest.fail("Failed to commit sample tags for tags_api.")

        tag_ids = {}
        for key, tag_obj in tags.items():
            if tag_obj.id is None: db.session.refresh(tag_obj)
            if tag_obj.id is None: pytest.fail(f"Tag '{key}' failed to get ID in tags_api fixture.")
            tag_ids[key] = tag_obj.id
        yield tag_ids


@pytest.fixture(scope="function")
def sample_deck_data(app, db, test_user):
    """Creates a sample deck for the primary test user."""
    user_id = test_user["user_obj"].id
    deck_name = "Tag Test Deck Tags Sesh"
    deck_type_id = 1 # Example type
    with app.app_context():
        # Ensure DeckType exists
        deck_type = db.session.get(DeckType, deck_type_id)
        if not deck_type:
            deck_type = DeckType(id=deck_type_id, name='Standard Tags Test')
            db.session.add(deck_type)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                deck_type = db.session.get(DeckType, deck_type_id)
                if not deck_type: pytest.fail("Failed to create/get DeckType in tags_api fixture.")

        stmt = select(Deck).where(Deck.user_id == user_id, Deck.name == deck_name)
        deck = db.session.scalars(stmt).first()
        if not deck:
            deck = Deck(user_id=user_id, name=deck_name, deck_type_id=deck_type.id)
            db.session.add(deck)
            try:
                db.session.commit()
                db.session.refresh(deck)
            except Exception as e:
                 db.session.rollback()
                 logger.error(f"Error committing deck in tags_api fixture: {e}")
                 pytest.fail("Failed to commit sample deck for tags_api.")
        elif deck.id is None:
             db.session.refresh(deck)

        if deck.id is None: pytest.fail("Failed to get deck ID in tags_api fixture.")

        yield {"id": deck.id, "name": deck.name, "user_id": user_id}


@pytest.fixture(scope="function")
def deck_with_tag_data(app, db, sample_deck_data, sample_tags_data):
    """Associates a specific tag with the sample deck."""
    with app.app_context():
        deck_id = sample_deck_data["id"]
        tag_id = sample_tags_data["competitive_tags_s"] # Use a specific tag
        deck = db.session.get(Deck, deck_id)
        tag = db.session.get(Tag, tag_id)

        if not deck: pytest.fail(f"Deck {deck_id} not found in deck_with_tag_data fixture.")
        if not tag: pytest.fail(f"Tag {tag_id} not found in deck_with_tag_data fixture.")

        if tag not in deck.tags:
            deck.tags.append(tag)
            try:
                db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 logger.error(f"Error committing deck tag association in fixture: {e}")
                 pytest.fail("Failed to commit deck tag association.")

        yield {"deck_id": deck_id, "tag_id": tag_id}


# --- Test Cases: GET Tags ---

def test_get_tags_success_no_tags(logged_in_client):
    client, _ = logged_in_client
    response = client.get("/api/tags")
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_tags_success_with_tags(logged_in_client, sample_tags_data):
    client, _ = logged_in_client
    response = client.get("/api/tags")
    assert response.status_code == 200
    tags_list = response.get_json()
    assert isinstance(tags_list, list)
    # Check if at least the expected tags are present
    expected_ids = set(sample_tags_data.values())
    returned_ids = {tag['id'] for tag in tags_list}
    assert expected_ids.issubset(returned_ids)


# --- Test Cases: POST Tag ---

def test_create_tag_success(logged_in_client):
    client, csrf_token = logged_in_client
    tag_name = "new_test_tag_api"
    payload = {"name": tag_name}
    response = client.post("/api/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data is not None
    assert json_data.get("name") == tag_name.lower() # Check normalization
    assert isinstance(json_data.get("id"), int)


def test_create_tag_duplicate(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    tag_name = "competitive_tags_s" # Name created by fixture
    payload = {"name": tag_name}
    response = client.post("/api/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 409 # Conflict


def test_create_tag_missing_name(logged_in_client):
    client, csrf_token = logged_in_client
    payload = {}
    response = client.post("/api/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 400


def test_create_tag_empty_name(logged_in_client):
    client, csrf_token = logged_in_client
    payload = {"name": "   "}
    response = client.post("/api/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 400


# --- Test Cases: Add Tag to Deck ---

def test_add_tag_to_deck_success(logged_in_client, sample_deck_data, sample_tags_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"] # Use a tag not added by deck_with_tag_data
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 201


def test_add_tag_to_deck_already_associated(logged_in_client, deck_with_tag_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"] # Tag already associated by fixture
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 200 # Should return OK if already associated


def test_add_tag_to_deck_deck_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_deck_id = 99999
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{invalid_deck_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404


def test_add_tag_to_deck_tag_not_found(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 99999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404


def test_add_tag_to_deck_deck_not_owned(logged_in_client_user_2, sample_deck_data, sample_tags_data):
    client, csrf_token = logged_in_client_user_2
    deck_id = sample_deck_data["id"] # Deck owned by user 1
    tag_id = sample_tags_data["budget_tags_s"] # Tag owned by user 1
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404 # Deck not owned by user 2


def test_add_tag_to_deck_tag_not_owned(app, db, logged_in_client, sample_deck_data, test_user_2):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"] # Deck owned by user 1
    user_2_id = test_user_2["user_obj"].id

    # Create tag owned by user 2
    tag_name_user_2 = "user2_decktag_owned_test"
    with app.app_context():
        stmt = select(Tag).where(Tag.user_id == user_2_id, Tag.name == tag_name_user_2)
        tag_user_2 = db.session.scalars(stmt).first()
        if not tag_user_2:
            tag_user_2 = Tag(user_id=user_2_id, name=tag_name_user_2)
            db.session.add(tag_user_2)
            try:
                db.session.commit()
                db.session.refresh(tag_user_2)
            except Exception as e:
                 db.session.rollback()
                 pytest.fail(f"Failed to create tag for user 2: {e}")
        if tag_user_2.id is None: pytest.fail("Failed to get ID for user 2 tag.")
        tag_id_user_2 = tag_user_2.id

    payload = {"tag_id": tag_id_user_2}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404 # Tag not owned by user 1


def test_add_tag_to_deck_missing_tag_id(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    payload = {}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 400


def test_add_tag_to_deck_unauthenticated(client, sample_deck_data, sample_tags_data):
    # *** CORRECTED TEST ***
    with client.session_transaction() as sess:
        sess.clear() # Ensure session is clear
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload)
    assert response.status_code == 401

# --- Test Cases: Remove Tag from Deck ---

def test_remove_tag_from_deck_success(logged_in_client, deck_with_tag_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 204


def test_remove_tag_from_deck_not_associated(logged_in_client, deck_with_tag_data, sample_tags_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id_not_associated = sample_tags_data["budget_tags_s"] # Use a tag not added by fixture
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id_not_associated}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404


def test_remove_tag_from_deck_deck_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_deck_id = 99999
    tag_id = sample_tags_data["competitive_tags_s"]
    response = client.delete(f"/api/decks/{invalid_deck_id}/tags/{tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404


def test_remove_tag_from_deck_tag_not_found(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 99999
    response = client.delete(f"/api/decks/{deck_id}/tags/{invalid_tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404


def test_remove_tag_from_deck_deck_not_owned(logged_in_client_user_2, deck_with_tag_data):
    client, csrf_token = logged_in_client_user_2
    deck_id = deck_with_tag_data["deck_id"] # Deck owned by user 1
    tag_id = deck_with_tag_data["tag_id"] # Tag owned by user 1
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == 404


def test_remove_tag_from_deck_unauthenticated(client, deck_with_tag_data):
    # *** CORRECTED TEST ***
    with client.session_transaction() as sess:
        sess.clear() # Ensure session is clear
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}")
    assert response.status_code == 401