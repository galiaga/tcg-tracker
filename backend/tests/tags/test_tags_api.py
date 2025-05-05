# backend/tests/tags/test_tags_api.py

# --- Imports ---
import pytest
from flask_bcrypt import Bcrypt
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import logging

from backend import db as _db
from backend.models import User, Tag, Deck, DeckType

# --- Fixtures ---

bcrypt = Bcrypt()
logger = logging.getLogger(__name__)

# NOTE: Assuming test_user, test_user_2, logged_in_client, logged_in_client_user_2
#       are correctly defined in conftest.py now.

@pytest.fixture(scope="function")
def sample_tags_data(app, db, test_user):
    """Creates sample tags for the primary test user."""
    user_id = test_user["user_obj"].id
    tags = {}
    tag_names = ["competitive_tags_s", "budget_tags_s", "testing_tags_s"]
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
    deck_type_id = 1
    with app.app_context():
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
        else:
            # Ensure tags are cleared if deck exists from previous run
            # Eager load tags before clearing
            deck_with_tags = db.session.get(Deck, deck.id, options=[selectinload(Deck.tags)])
            if deck_with_tags and deck_with_tags.tags:
                logger.info(f"Clearing tags from reused deck {deck.id} in sample_deck_data fixture.")
                deck_with_tags.tags.clear()
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error clearing tags from existing deck in fixture: {e}")

        if deck.id is None: pytest.fail("Failed to get deck ID in tags_api fixture.")

        yield {"id": deck.id, "name": deck.name, "user_id": user_id}


@pytest.fixture(scope="function")
def deck_with_tag_data(app, db, sample_deck_data, sample_tags_data):
    """Associates a specific tag with the sample deck."""
    with app.app_context():
        deck_id = sample_deck_data["id"]
        tag_id = sample_tags_data["competitive_tags_s"]
        deck = db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
        tag = db.session.get(Tag, tag_id)

        if not deck: pytest.fail(f"Deck {deck_id} not found in deck_with_tag_data fixture")
        if not tag: pytest.fail(f"Tag {tag_id} not found in deck_with_tag_data fixture")

        if tag not in deck.tags:
            logger.info(f"Associating tag {tag_id} with deck {deck_id} in deck_with_tag_data fixture.")
            deck.tags.append(tag)
            try:
                db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 logger.error(f"Error committing deck tag association in fixture: {e}")
                 pytest.fail("Failed to commit deck tag association.")
        else:
            logger.info(f"Tag {tag_id} already associated with deck {deck_id} in deck_with_tag_data fixture.")

        yield {"deck_id": deck_id, "tag_id": tag_id}

# --- Test Cases: GET Tags ---

def test_get_tags_success_no_tags(app, db, logged_in_client, test_user):
    client, _ = logged_in_client
    user_id = test_user["user_obj"].id
    with app.app_context():
        stmt = delete(Tag).where(Tag.user_id == user_id)
        _db.session.execute(stmt)
        _db.session.commit()

    response = client.get("/api/tags")
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_tags_success_with_tags(logged_in_client, sample_tags_data):
    client, _ = logged_in_client
    response = client.get("/api/tags")
    json_response = response.get_json()
    assert response.status_code == 200
    assert isinstance(json_response, list)
    expected_ids = set(sample_tags_data.values())
    returned_ids = {tag['id'] for tag in json_response}
    assert expected_ids.issubset(returned_ids)


def test_get_tags_unauthenticated(client):
    # *** ADDED SESSION CLEAR ***
    with client.session_transaction() as sess:
        sess.clear()
    response = client.get("/api/tags")
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]

# --- Test Cases: Create Tag ---

def test_create_tag_success(app, db, logged_in_client, test_user):
    client, csrf_token = logged_in_client
    user_id = test_user["user_obj"].id
    payload = {"name": "new_test_tag_api"}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    json_response = response.get_json()

    assert response.status_code == 201
    assert json_response["name"] == "new_test_tag_api"
    assert isinstance(json_response.get("id"), int)

    with app.app_context():
        tag = _db.session.get(Tag, json_response["id"])
        assert tag is not None
        assert tag.name == "new_test_tag_api"
        assert tag.user_id == user_id


def test_create_tag_duplicate(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    payload = {"name": "competitive_tags_s"}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 409


def test_create_tag_missing_name(logged_in_client):
    client, csrf_token = logged_in_client
    payload = {}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    assert "Missing 'name'" in response.get_json().get("error", "")


def test_create_tag_empty_name(logged_in_client):
    client, csrf_token = logged_in_client
    payload = {"name": "   "}
    response = client.post(
        "/api/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    assert "must be a non-empty string" in response.get_json().get("error", "")


def test_create_tag_unauthenticated(client):
    # *** ADDED SESSION CLEAR ***
    with client.session_transaction() as sess:
        sess.clear()
    payload = {"name": "Auth Test Session"}
    response = client.post("/api/tags", json=payload)
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]

# --- Test Cases: Add Tag to Deck ---

def test_add_tag_to_deck_success(app, db, logged_in_client, sample_deck_data, sample_tags_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}

    # *** ADDED EXPLICIT CLEANUP FOR THIS TEST ***
    with app.app_context():
        deck = db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
        tag = db.session.get(Tag, tag_id)
        if deck and tag and tag in deck.tags:
            logger.warning(f"Explicitly removing tag {tag_id} from deck {deck_id} before test_add_tag_to_deck_success")
            deck.tags.remove(tag)
            db.session.commit()
    # *** END CLEANUP ***

    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )

    # *** CORRECTED ASSERTION ***
    assert response.status_code == 201 # Expect 201 Created
    assert "Tag associated successfully" in response.get_json().get("message", "")

    with app.app_context():
        reloaded_deck = _db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
        assert reloaded_deck is not None
        tag_ids_on_deck = {tag.id for tag in reloaded_deck.tags}
        assert tag_id in tag_ids_on_deck


def test_add_tag_to_deck_already_associated(logged_in_client, deck_with_tag_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    payload = {"tag_id": tag_id}

    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 200
    assert "Tag already associated" in response.get_json().get("message", "")


def test_add_tag_to_deck_deck_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_deck_id = 99999
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/decks/{invalid_deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_tag_not_found(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 99999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_deck_not_owned(logged_in_client_user_2, sample_deck_data, sample_tags_data):
    client, csrf_token = logged_in_client_user_2
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_tag_not_owned(app, db, logged_in_client, sample_deck_data, test_user_2):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    user_2_id = test_user_2["user_obj"].id

    tag_name_user_2 = "user2tag_owned_s"
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
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_deck_missing_tag_id(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    payload = {}
    response = client.post(
        f"/api/decks/{deck_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400


def test_add_tag_to_deck_unauthenticated(client, sample_deck_data, sample_tags_data):
    # *** ADDED SESSION CLEAR ***
    with client.session_transaction() as sess:
        sess.clear()
    deck_id = sample_deck_data["id"]
    tag_id = sample_tags_data["budget_tags_s"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/decks/{deck_id}/tags", json=payload)
    assert response.status_code == 401

# --- Test Cases: Remove Tag from Deck ---

def test_remove_tag_from_deck_success(app, db, logged_in_client, deck_with_tag_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(
        f"/api/decks/{deck_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 204

    with app.app_context():
        reloaded_deck = _db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
        assert reloaded_deck is not None
        tag_ids_on_deck = {tag.id for tag in reloaded_deck.tags}
        assert tag_id not in tag_ids_on_deck


def test_remove_tag_from_deck_not_associated(logged_in_client, deck_with_tag_data, sample_tags_data):
    client, csrf_token = logged_in_client
    deck_id = deck_with_tag_data["deck_id"]
    tag_id_not_associated = sample_tags_data["budget_tags_s"]

    response = client.delete(
        f"/api/decks/{deck_id}/tags/{tag_id_not_associated}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404
    json_response = response.get_json()
    if json_response:
        assert "Tag is not associated" in json_response.get("error", "")


def test_remove_tag_from_deck_deck_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_deck_id = 99999
    tag_id = sample_tags_data["competitive_tags_s"]
    response = client.delete(
        f"/api/decks/{invalid_deck_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_deck_tag_not_found(logged_in_client, sample_deck_data):
    client, csrf_token = logged_in_client
    deck_id = sample_deck_data["id"]
    invalid_tag_id = 99999
    response = client.delete(
        f"/api/decks/{deck_id}/tags/{invalid_tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_deck_deck_not_owned(logged_in_client_user_2, deck_with_tag_data):
    client, csrf_token = logged_in_client_user_2
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(
        f"/api/decks/{deck_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_deck_unauthenticated(client, deck_with_tag_data):
    # *** ADDED SESSION CLEAR ***
    with client.session_transaction() as sess:
        sess.clear()
    deck_id = deck_with_tag_data["deck_id"]
    tag_id = deck_with_tag_data["tag_id"]
    response = client.delete(f"/api/decks/{deck_id}/tags/{tag_id}")
    assert response.status_code == 401

# --- Moved Tests ---
# Moved test_get_tags_unauthenticated and test_create_tag_unauthenticated here

def test_get_tags_unauthenticated(client):
    # *** ADDED SESSION CLEAR ***
    with client.session_transaction() as sess:
        sess.clear()
    response = client.get("/api/tags")
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]


def test_create_tag_unauthenticated(client):
    # *** ADDED SESSION CLEAR ***
    with client.session_transaction() as sess:
        sess.clear()
    payload = {"name": "Auth Test Session"}
    response = client.post("/api/tags", json=payload)
    assert response.status_code == 401
    json_response = response.get_json()
    assert json_response is not None and "msg" in json_response
    assert "Authentication required" in json_response["msg"]