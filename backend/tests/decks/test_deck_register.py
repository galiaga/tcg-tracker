import pytest
from backend.models import User, Commander, Deck, DeckType, UserDeck, CommanderDeck
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt

@pytest.fixture(scope='function')
def test_user(app, db):
    bcrypt = Bcrypt(app)
    with app.app_context():
        hashed_password = bcrypt.generate_password_hash("password123").decode("utf-8")
        user = User(username="decktestuser_conftest", hash=hashed_password)
        db.session.add(user)
        db.session.commit()
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
def commanders(app, db):
    with app.app_context():
        deck_types = [
            {'id': 1, 'name': 'Standard'}, {'id': 2, 'name': 'Pioneer'},
            {'id': 3, 'name': 'Modern'}, {'id': 4, 'name': 'Legacy'},
            {'id': 5, 'name': 'Vintage'}, {'id': 6, 'name': 'Pauper'},
            {'id': 7, 'name': 'Commander / EDH'}
        ]
        for dt_data in deck_types:
                dt = DeckType(**dt_data)
                db.session.merge(dt)
        db.session.commit()

        cmdrs_data = {
            "no_partner": {"name": "Solo Commander", "scryfall_id": "solo1", "partner": False},
            "can_partner_1": {"name": "Partner Commander 1", "scryfall_id": "p1", "partner": True},
            "can_partner_2": {"name": "Partner Commander 2", "scryfall_id": "p2", "partner": True},
            "ff_1": {"name": "FF Commander 1", "scryfall_id": "ff1", "friends_forever": True},
            "ff_2": {"name": "FF Commander 2", "scryfall_id": "ff2", "friends_forever": True},
            "doctor": {"name": "The Doctor", "scryfall_id": "doc1", "time_lord_doctor": True},
            "companion": {"name": "The Companion", "scryfall_id": "comp1", "doctor_companion": True},
            "needs_bg": {"name": "Needs Background", "scryfall_id": "nbg1", "choose_a_background": True},
            "is_bg": {"name": "Is Background", "scryfall_id": "bg1", "background": True},
            "invalid_partner": {"name": "Not A Real Partner", "scryfall_id": "invp1", "partner": False},
            "invalid_ff": {"name": "Not A Real FF", "scryfall_id": "invff1", "friends_forever": False},
            "invalid_bg": {"name": "Not A Real BG", "scryfall_id": "invbg1", "background": False},
            "invalid_doctor": {"name": "Not A Real Doctor", "scryfall_id": "invdoc1", "time_lord_doctor": False},
            "invalid_companion": {"name": "Not A Real Companion", "scryfall_id": "invcomp1", "doctor_companion": False}
        }
        cmdrs = {}
        for key, data in cmdrs_data.items():
            cmdr = Commander(**data)
            db.session.add(cmdr)
            cmdrs[key] = cmdr
        db.session.commit()
        for k in cmdrs:
             db.session.refresh(cmdrs[k])
        yield cmdrs


def test_register_simple_commander_success(client, app, db, auth_headers, commanders):
    with app.app_context():
        payload = {
            "deck_name": "Simple Commander Deck",
            "deck_type": 7,
            "commander_id": commanders["no_partner"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["message"] == "Deck registered successfully"
        assert json_response["deck"]["name"] == "Simple Commander Deck"
        assert json_response["deck"]["commander_id"] == commanders["no_partner"].id
        assert json_response["deck"]["partner_id"] is None

        deck = db.session.query(Deck).filter_by(name="Simple Commander Deck").first()
        assert deck is not None
        assert deck.deck_type_id == 7
        cmd_deck = db.session.query(CommanderDeck).filter_by(deck_id=deck.id).first()
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["no_partner"].id
        assert cmd_deck.associated_commander_id is None


def test_register_valid_partner_success(client, app, db, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Partner Power",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"].id,
            "partner_id": commanders["can_partner_2"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["message"] == "Deck registered successfully"
        assert json_response["deck"]["commander_id"] == commanders["can_partner_1"].id
        assert json_response["deck"]["partner_id"] == commanders["can_partner_2"].id
        assert json_response["deck"]["friends_forever_id"] is None

        deck = db.session.query(Deck).filter_by(name="Partner Power").first()
        assert deck is not None
        cmd_deck = db.session.query(CommanderDeck).filter_by(deck_id=deck.id).first()
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["can_partner_1"].id
        assert cmd_deck.associated_commander_id == commanders["can_partner_2"].id


def test_register_valid_ff_success(client, app, db, auth_headers, commanders):
    with app.app_context():
        payload = {
            "deck_name": "BFF Deck",
            "deck_type": 7,
            "commander_id": commanders["ff_1"].id,
            "friends_forever_id": commanders["ff_2"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["deck"]["commander_id"] == commanders["ff_1"].id
        assert json_response["deck"]["friends_forever_id"] == commanders["ff_2"].id
        assert json_response["deck"]["partner_id"] is None

        deck = db.session.query(Deck).filter_by(name="BFF Deck").first()
        assert deck is not None
        cmd_deck = db.session.query(CommanderDeck).filter_by(deck_id=deck.id).first()
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["ff_1"].id
        assert cmd_deck.associated_commander_id == commanders["ff_2"].id


def test_register_valid_doctor_companion_success(client, app, db, auth_headers, commanders):
    with app.app_context():
        payload = {
            "deck_name": "TARDIS Crew",
            "deck_type": 7,
            "commander_id": commanders["doctor"].id,
            "doctor_companion_id": commanders["companion"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["deck"]["commander_id"] == commanders["doctor"].id
        assert json_response["deck"]["doctor_companion_id"] == commanders["companion"].id
        assert json_response["deck"]["time_lord_doctor_id"] is None

        deck = db.session.query(Deck).filter_by(name="TARDIS Crew").first()
        assert deck is not None
        cmd_deck = db.session.query(CommanderDeck).filter_by(deck_id=deck.id).first()
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["doctor"].id
        assert cmd_deck.associated_commander_id == commanders["companion"].id

def test_register_valid_choose_background_success(client, app, db, auth_headers, commanders):
    with app.app_context():
        payload = {
            "deck_name": "Background Story",
            "deck_type": 7,
            "commander_id": commanders["needs_bg"].id,
            "background_id": commanders["is_bg"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["deck"]["commander_id"] == commanders["needs_bg"].id
        assert json_response["deck"]["background_id"] == commanders["is_bg"].id

        deck = db.session.query(Deck).filter_by(name="Background Story").first()
        assert deck is not None
        cmd_deck = db.session.query(CommanderDeck).filter_by(deck_id=deck.id).first()
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["needs_bg"].id
        assert cmd_deck.associated_commander_id == commanders["is_bg"].id

def test_fail_missing_commander_id(client, app, auth_headers):
     with app.app_context():
        payload = {
            "deck_name": "No Commander Deck",
            "deck_type": 7
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert "Add your Commander" in json_response.get("error", "")

def test_fail_missing_required_partner(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Needs Partner Deck",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['can_partner_1'].name}' requires a Partner commander" in json_response.get("error", "")

def test_fail_missing_required_ff(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Needs FF Deck",
            "deck_type": 7,
            "commander_id": commanders["ff_1"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['ff_1'].name}' requires a Friends Forever commander" in json_response.get("error", "")


def test_fail_missing_required_companion(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Needs Companion Deck",
            "deck_type": 7,
            "commander_id": commanders["doctor"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['doctor'].name}' requires a Doctor's Companion commander" in json_response.get("error", "")

def test_fail_missing_required_doctor(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Needs Doctor Deck",
            "deck_type": 7,
            "commander_id": commanders["companion"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['companion'].name}' requires a Time Lord Doctor commander" in json_response.get("error", "")

def test_fail_missing_required_background(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Needs Background Deck",
            "deck_type": 7,
            "commander_id": commanders["needs_bg"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['needs_bg'].name}' requires a Background commander" in json_response.get("error", "")


def test_fail_invalid_main_commander_for_partner(client, app, auth_headers, commanders):
    with app.app_context():
        payload = {
            "deck_name": "Invalid Main For Partner",
            "deck_type": 7,
            "commander_id": commanders["no_partner"].id,
            "partner_id": commanders["can_partner_1"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['no_partner'].name}' cannot be paired with the selected Partner" in json_response.get("error", "")


def test_fail_invalid_associated_commander_for_partner(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Invalid Associated Partner",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"].id,
            "partner_id": commanders["invalid_partner"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['invalid_partner'].name}' is not a valid Partner" in json_response.get("error", "")

def test_fail_invalid_associated_commander_for_ff(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Invalid Associated FF",
            "deck_type": 7,
            "commander_id": commanders["ff_1"].id,
            "friends_forever_id": commanders["invalid_ff"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['invalid_ff'].name}' is not a valid Friends Forever" in json_response.get("error", "")


def test_fail_invalid_associated_commander_for_background(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Invalid Associated Background",
            "deck_type": 7,
            "commander_id": commanders["needs_bg"].id,
            "background_id": commanders["invalid_bg"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['invalid_bg'].name}' is not a valid Background" in json_response.get("error", "")

def test_fail_invalid_associated_commander_for_doctor(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Invalid Associated Doctor",
            "deck_type": 7,
            "commander_id": commanders["companion"].id,
            "time_lord_doctor_id": commanders["invalid_doctor"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['invalid_doctor'].name}' is not a valid Time Lord Doctor" in json_response.get("error", "")

def test_fail_invalid_associated_commander_for_companion(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Invalid Associated Companion",
            "deck_type": 7,
            "commander_id": commanders["doctor"].id,
            "doctor_companion_id": commanders["invalid_companion"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert f"'{commanders['invalid_companion'].name}' is not a valid Doctor Companion" in json_response.get("error", "")


def test_fail_commander_equals_partner(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Same Commander Partner",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"].id,
            "partner_id": commanders["can_partner_1"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert "Commander and associated Commander cannot be the same" in json_response.get("error", "")

def test_fail_multiple_associated_ids(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_name": "Too Many Partners",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"].id,
            "partner_id": commanders["can_partner_2"].id,
            "friends_forever_id": commanders["ff_1"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert "Only one associated commander type" in json_response.get("error", "")

def test_fail_deck_name_missing(client, app, auth_headers, commanders):
     with app.app_context():
        payload = {
            "deck_type": 7,
            "commander_id": commanders["no_partner"].id
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        assert response.status_code == 400
        assert "Add a Deck Name" in json_response.get("error", "")

def test_fail_not_authenticated(client, app, commanders):
    with app.app_context():
        cmdr_id = commanders["no_partner"].id
        payload = {
            "deck_name": "Auth Test Deck",
            "deck_type": 7,
            "commander_id": cmdr_id
        }
        response = client.post("/api/register_deck", json=payload)
        assert response.status_code == 401

def test_invalid_partner_combination(client, app, auth_headers, commanders):
    with app.app_context():
        payload = {
            "deck_name": "Test Deck Invalid Main Confirmed",
            "deck_type": 7,
            "commander_id": commanders["no_partner"].id, 
            "partner_id": commanders["can_partner_1"].id 
        }
        response = client.post("/api/register_deck", json=payload, headers=auth_headers)
        json_response = response.get_json()

        print("🧪 RESPONSE (Original Test):", response.status_code, json_response)

        assert response.status_code == 400
        assert json_response is not None
        assert "cannot be paired" in json_response.get("error", "")