# backend/tests/matches/test_match_tags_api.py

# --- Imports ---
import pytest
from flask_bcrypt import Bcrypt
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import logging

from backend import db as _db
from backend.models import User, Tag, Deck, DeckType, LoggedMatch, Commander

# --- Fixtures ---

bcrypt = Bcrypt()
logger = logging.getLogger(__name__)

# NOTE: Assuming test_user, test_user_2, logged_in_client, logged_in_client_user_2
#       are correctly defined in conftest.py now.

@pytest.fixture(scope='function')
def sample_tags_data(app, db, test_user):
    """Sets up sample tags for the primary test user."""
    user_id = test_user["user_obj"].id
    with app.app_context():
        tags = {}
        tag_names = ["mt_api_comp", "mt_api_budget", "mt_api_test", "mt_api_user2tag"]
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
                 logger.error(f"Error committing tags in fixture: {e}")
                 pytest.fail("Failed to commit sample tags.")

        tag_ids = {}
        for key, tag_obj in tags.items():
             if tag_obj.id is None: db.session.refresh(tag_obj)
             if tag_obj.id is None: pytest.fail(f"Tag '{key}' failed to get ID.")
             tag_ids[key] = tag_obj.id
        yield tag_ids


@pytest.fixture(scope='function')
def sample_deck_data_for_match(app, db, test_user):
    """Sets up a sample deck for the primary test user."""
    user_id = test_user["user_obj"].id
    deck_name = "Match Tag API Test Deck"
    deck_type_id = 1
    with app.app_context():
        deck_type = db.session.get(DeckType, deck_type_id)
        if not deck_type:
            deck_type = DeckType(id=deck_type_id, name='Standard API Test')
            db.session.add(deck_type)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                deck_type = db.session.get(DeckType, deck_type_id)
                if not deck_type: pytest.fail("Failed to create/get DeckType.")

        stmt_deck = select(Deck).where(Deck.name == deck_name, Deck.user_id == user_id)
        deck = db.session.scalars(stmt_deck).first()

        if not deck:
            deck = Deck(name=deck_name, deck_type_id=deck_type.id, user_id=user_id)
            db.session.add(deck)
            try:
                db.session.commit()
                db.session.refresh(deck)
            except Exception as e:
                 db.session.rollback()
                 logger.error(f"Error committing deck in fixture: {e}")
                 pytest.fail("Failed to commit sample deck.")
        elif deck.id is None:
             db.session.refresh(deck)

        if deck.id is None: pytest.fail("Failed to get deck ID.")
        yield {"id": deck.id, "user_id": user_id}


@pytest.fixture(scope='function')
def sample_logged_match_data(app, db, test_user, sample_deck_data_for_match):
    """Sets up a sample LoggedMatch for the primary test user's deck."""
    user_id = test_user["user_obj"].id
    deck_id = sample_deck_data_for_match["id"]
    with app.app_context():
        stmt = (select(LoggedMatch)
            .where(LoggedMatch.logger_user_id == user_id,
                   LoggedMatch.deck_id == deck_id,
                   LoggedMatch.result == 0) # Using result 0 (Loss)
            .order_by(LoggedMatch.timestamp.desc())
        )
        match = db.session.scalars(stmt).first()

        needs_commit = False
        if not match:
            logger.info("Creating new LoggedMatch in fixture (sample_logged_match_data)")
            match = LoggedMatch(
                logger_user_id=user_id,
                deck_id=deck_id,
                result=0,
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(match)
            needs_commit = True
        else:
             logger.info(f"Reusing existing LoggedMatch {match.id} in fixture, clearing tags.")
             match_with_tags = db.session.get(LoggedMatch, match.id, options=[selectinload(LoggedMatch.tags)])
             if match_with_tags and match_with_tags.tags:
                 logger.info(f"Tags found on reused match {match.id}: {[t.id for t in match_with_tags.tags]}")
                 match_with_tags.tags.clear()
                 needs_commit = True
             else:
                 logger.info(f"No tags found on reused match {match.id} or relationship not loaded.")

        if needs_commit:
            try:
                db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 logger.error(f"Error committing LoggedMatch in fixture: {e}")
                 pytest.fail("Failed to commit sample LoggedMatch.")

        if match.id is None: db.session.refresh(match)
        if match.id is None: pytest.fail("Failed to get LoggedMatch ID.")

        yield {"id": match.id, "user_id": user_id}


@pytest.fixture(scope='function')
def logged_match_with_tag_data(app, db, sample_logged_match_data, sample_tags_data):
    """Ensures a specific tag is associated with the sample LoggedMatch."""
    with app.app_context():
        match_id = sample_logged_match_data["id"]
        tag_id = sample_tags_data["mt_api_comp"]
        match = db.session.get(LoggedMatch, match_id, options=[selectinload(LoggedMatch.tags)])
        tag = db.session.get(Tag, tag_id)

        if not match: pytest.fail(f"LoggedMatch with id {match_id} not found in fixture setup.")
        if not tag: pytest.fail(f"Tag with id {tag_id} not found in fixture setup.")

        if tag not in match.tags:
             logger.info(f"Associating tag {tag_id} with LoggedMatch {match_id} in fixture.")
             match.tags.append(tag)
             try:
                 db.session.commit()
             except Exception as e:
                  db.session.rollback()
                  logger.error(f"Error committing tag association in fixture: {e}")
                  pytest.fail("Failed to commit tag association.")
        else:
             logger.info(f"Tag {tag_id} already associated with LoggedMatch {match_id} in fixture.")

        yield {"match_id": match_id, "tag_id": tag_id}


# --- Test Cases: Add Tag ---

def test_add_tag_to_match_success(app, db, logged_in_client, sample_logged_match_data, sample_tags_data):
    client, csrf_token = logged_in_client
    match_id = sample_logged_match_data["id"]
    tag_id = sample_tags_data["mt_api_budget"]
    payload = {"tag_id": tag_id}

    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    # *** CORRECTED ASSERTION ***
    assert response.status_code == 201 # Route should return 201
    assert "Tag associated successfully" in response.get_json().get("message", "")

    with app.app_context():
        reloaded_match = db.session.get(LoggedMatch, match_id, options=[selectinload(LoggedMatch.tags)])
        assert reloaded_match is not None
        tag_ids_on_match = {tag.id for tag in reloaded_match.tags}
        assert tag_id in tag_ids_on_match


def test_add_tag_to_match_already_associated(logged_in_client, logged_match_with_tag_data):
    client, csrf_token = logged_in_client
    match_id = logged_match_with_tag_data["match_id"]
    tag_id = logged_match_with_tag_data["tag_id"]
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
    tag_id = sample_tags_data["mt_api_budget"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/matches/{invalid_match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_tag_not_found(logged_in_client, sample_logged_match_data):
    client, csrf_token = logged_in_client
    match_id = sample_logged_match_data["id"]
    invalid_tag_id = 99999
    payload = {"tag_id": invalid_tag_id}
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_match_not_owned(logged_in_client_user_2, sample_logged_match_data, sample_tags_data):
    client, csrf_token = logged_in_client_user_2
    match_id = sample_logged_match_data["id"]
    tag_id = sample_tags_data["mt_api_budget"]
    payload = {"tag_id": tag_id}
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_tag_not_owned(app, db, logged_in_client, sample_logged_match_data, test_user_2):
    client, csrf_token = logged_in_client
    match_id = sample_logged_match_data["id"]
    user_2_id = test_user_2["user_obj"].id
    tag_name_user_2 = "user2_matchtag_owned_api_test"
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
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_add_tag_to_match_missing_tag_id(logged_in_client, sample_logged_match_data):
    client, csrf_token = logged_in_client
    match_id = sample_logged_match_data["id"]
    payload = {}
    response = client.post(
        f"/api/matches/{match_id}/tags",
        json=payload,
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 400
    json_response = response.get_json()
    assert json_response is not None
    assert "Missing 'tag_id'" in json_response.get("error", "")


def test_add_tag_to_match_unauthenticated(client, sample_logged_match_data, sample_tags_data):
    # *** CORRECTED TEST ***
    with client.session_transaction() as sess:
        sess.clear() # Ensure session is clear
    match_id = sample_logged_match_data["id"]
    tag_id = sample_tags_data["mt_api_budget"]
    payload = {"tag_id": tag_id}
    response = client.post(f"/api/matches/{match_id}/tags", json=payload)
    assert response.status_code == 401 # Expect 401


# --- Test Cases: Remove Tag ---

def test_remove_tag_from_match_success(app, db, logged_in_client, logged_match_with_tag_data):
    client, csrf_token = logged_in_client
    match_id = logged_match_with_tag_data["match_id"]
    tag_id = logged_match_with_tag_data["tag_id"]

    response = client.delete(
        f"/api/matches/{match_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 204

    with app.app_context():
        reloaded_match = db.session.get(LoggedMatch, match_id, options=[selectinload(LoggedMatch.tags)])
        assert reloaded_match is not None
        tag_ids_on_match = {tag.id for tag in reloaded_match.tags}
        assert tag_id not in tag_ids_on_match


def test_remove_tag_from_match_not_associated(logged_in_client, logged_match_with_tag_data, sample_tags_data):
    client, csrf_token = logged_in_client
    match_id = logged_match_with_tag_data["match_id"]
    tag_id_not_associated = sample_tags_data["mt_api_budget"] # This tag is NOT added by logged_match_with_tag_data

    response = client.delete(
        f"/api/matches/{match_id}/tags/{tag_id_not_associated}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    # *** CORRECTED ASSERTION ***
    assert response.status_code == 404 # Route logic now returns 404
    json_response = response.get_json()
    if json_response:
        assert "Tag is not associated" in json_response.get("error", "")


def test_remove_tag_from_match_match_not_found(logged_in_client, sample_tags_data):
    client, csrf_token = logged_in_client
    invalid_match_id = 99999
    tag_id = sample_tags_data["mt_api_comp"]
    response = client.delete(
        f"/api/matches/{invalid_match_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_match_tag_not_found(logged_in_client, sample_logged_match_data):
    client, csrf_token = logged_in_client
    match_id = sample_logged_match_data["id"]
    invalid_tag_id = 99999
    response = client.delete(
        f"/api/matches/{match_id}/tags/{invalid_tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404 # Route checks association first, then tag existence implicitly


def test_remove_tag_from_match_match_not_owned(logged_in_client_user_2, logged_match_with_tag_data):
    client, csrf_token = logged_in_client_user_2
    match_id = logged_match_with_tag_data["match_id"]
    tag_id = logged_match_with_tag_data["tag_id"]
    response = client.delete(
        f"/api/matches/{match_id}/tags/{tag_id}",
        headers={"X-CSRF-TOKEN": csrf_token}
    )
    assert response.status_code == 404


def test_remove_tag_from_match_unauthenticated(client, logged_match_with_tag_data):
    # *** CORRECTED TEST ***
    with client.session_transaction() as sess:
        sess.clear() # Ensure session is clear
    match_id = logged_match_with_tag_data["match_id"]
    tag_id = logged_match_with_tag_data["tag_id"]
    response = client.delete(f"/api/matches/{match_id}/tags/{tag_id}")
    assert response.status_code == 401 # Expect 401