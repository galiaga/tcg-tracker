import pytest
from backend.models import User, Commander, Deck, DeckType, UserDeck, CommanderDeck
from flask_bcrypt import Bcrypt
from backend import db as _db
from sqlalchemy import select

@pytest.fixture(scope='function')
def test_user(app):
    bcrypt = Bcrypt(app)
    username = "decktestuser_session"
    password = "password123"
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

    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200
    csrf_token = csrf_resp.get_json()['csrf_token']
    assert csrf_token is not None

    yield client, csrf_token 


@pytest.fixture(scope='function')
def commanders(app):
    with app.app_context():
        deck_types_data = [
            {'id': 1, 'name': 'Standard'}, {'id': 2, 'name': 'Pioneer'},
            {'id': 3, 'name': 'Modern'}, {'id': 4, 'name': 'Legacy'},
            {'id': 5, 'name': 'Vintage'}, {'id': 6, 'name': 'Pauper'},
            {'id': 7, 'name': 'Commander / EDH'}
        ]
        for dt_data in deck_types_data:
            dt = _db.session.scalar(select(DeckType).where(DeckType.id == dt_data['id']))
            if not dt:
                dt = DeckType(**dt_data)
                _db.session.add(dt)
        _db.session.commit()

        cmdrs_data = {
            "no_partner": {"name": "Solo Cmdr Sesh", "scryfall_id": "solo1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "can_partner_1": {"name": "Partner Cmdr 1 Sesh", "scryfall_id": "p1_s", "partner": True, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "can_partner_2": {"name": "Partner Cmdr 2 Sesh", "scryfall_id": "p2_s", "partner": True, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "ff_1": {"name": "FF Cmdr 1 Sesh", "scryfall_id": "ff1_s", "partner": False, "friends_forever": True, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "ff_2": {"name": "FF Cmdr 2 Sesh", "scryfall_id": "ff2_s", "partner": False, "friends_forever": True, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "doctor": {"name": "The Doctor Sesh", "scryfall_id": "doc1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": True, "doctor_companion": False, "background": False},
            "companion": {"name": "The Companion Sesh", "scryfall_id": "comp1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": True, "background": False},
            "needs_bg": {"name": "Needs Background Sesh", "scryfall_id": "nbg1_s", "partner": False, "friends_forever": False, "choose_a_background": True, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "is_bg": {"name": "Is Background Sesh", "scryfall_id": "bg1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": True},
            "invalid_partner": {"name": "Not Partner Sesh", "scryfall_id": "invp1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_ff": {"name": "Not FF Sesh", "scryfall_id": "invff1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_bg": {"name": "Not BG Sesh", "scryfall_id": "invbg1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_doctor": {"name": "Not Doctor Sesh", "scryfall_id": "invdoc1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "invalid_companion": {"name": "Not Companion Sesh", "scryfall_id": "invcomp1_s", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False}
        }
        cmdrs = {}
        for key, data in cmdrs_data.items():
            cmdr = _db.session.scalar(select(Commander).where(Commander.scryfall_id == data['scryfall_id']))
            if not cmdr:
                cmdr = Commander(**data)
                _db.session.add(cmdr)
            cmdrs[key] = cmdr
        _db.session.commit()

        # Return IDs for use in tests
        commander_ids = {k: c.id for k, c in cmdrs.items()}
        yield commander_ids # Yielding IDs instead of objects


def test_register_simple_commander_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "Simple Commander Deck Session",
            "deck_type": 7,
            "commander_id": commanders["no_partner"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["message"] == "Deck registered successfully"
        assert json_response["deck"]["name"] == "Simple Commander Deck Session"
        assert json_response["deck"]["commander_id"] == commanders["no_partner"]
        assert json_response["deck"]["partner_id"] is None

        deck = deck = _db.session.scalar(select(Deck).where(Deck.name == "Simple Commander Deck Session"))
        assert deck is not None
        assert deck.deck_type_id == 7
        cmd_deck = _db.session.scalar(select(CommanderDeck).where(CommanderDeck.deck_id == deck.id))
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["no_partner"]
        assert cmd_deck.associated_commander_id is None


def test_register_valid_partner_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "Partner Power Session",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"],
            "partner_id": commanders["can_partner_2"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["message"] == "Deck registered successfully"
        assert json_response["deck"]["commander_id"] == commanders["can_partner_1"]
        assert json_response["deck"]["partner_id"] == commanders["can_partner_2"]
        assert json_response["deck"]["friends_forever_id"] is None

        deck = deck = _db.session.scalar(select(Deck).where(Deck.name == "Partner Power Session"))
        assert deck is not None
        cmd_deck = _db.session.scalar(select(CommanderDeck).where(CommanderDeck.deck_id == deck.id))
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["can_partner_1"]
        assert cmd_deck.associated_commander_id == commanders["can_partner_2"]


def test_register_valid_ff_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "BFF Deck Session",
            "deck_type": 7,
            "commander_id": commanders["ff_1"],
            "friends_forever_id": commanders["ff_2"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["deck"]["commander_id"] == commanders["ff_1"]
        assert json_response["deck"]["friends_forever_id"] == commanders["ff_2"]
        assert json_response["deck"]["partner_id"] is None

        deck = _db.session.scalar(select(Deck).where(Deck.name == "BFF Deck Session"))
        assert deck is not None
        cmd_deck = _db.session.scalar(select(CommanderDeck).where(CommanderDeck.deck_id == deck.id))
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["ff_1"]
        assert cmd_deck.associated_commander_id == commanders["ff_2"]


def test_register_valid_doctor_companion_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "TARDIS Crew Session",
            "deck_type": 7,
            "commander_id": commanders["doctor"],
            "doctor_companion_id": commanders["companion"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["deck"]["commander_id"] == commanders["doctor"]
        assert json_response["deck"]["doctor_companion_id"] == commanders["companion"]
        assert json_response["deck"]["time_lord_doctor_id"] is None

        deck = _db.session.scalar(select(Deck).where(Deck.name == "TARDIS Crew Session"))
        assert deck is not None
        cmd_deck = _db.session.scalar(select(CommanderDeck).where(CommanderDeck.deck_id == deck.id))
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["doctor"]
        assert cmd_deck.associated_commander_id == commanders["companion"]


def test_register_valid_choose_background_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "Background Story Session",
            "deck_type": 7,
            "commander_id": commanders["needs_bg"],
            "background_id": commanders["is_bg"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 201
        assert json_response["deck"]["commander_id"] == commanders["needs_bg"]
        assert json_response["deck"]["background_id"] == commanders["is_bg"]
        
        deck = _db.session.scalar(select(Deck).where(Deck.name == "Background Story Session"))
        assert deck is not None
        cmd_deck = _db.session.scalar(select(CommanderDeck).where(CommanderDeck.deck_id == deck.id))
        assert cmd_deck is not None
        assert cmd_deck.commander_id == commanders["needs_bg"]
        assert cmd_deck.associated_commander_id == commanders["is_bg"]


# --- Failure Cases ---

def test_fail_missing_commander_id(app, logged_in_client):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "No Commander Deck Session",
            "deck_type": 7
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert "Add your Commander" in json_response["error"]


def test_fail_missing_required_partner(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        main_cmdr = _db.session.get(Commander, commanders["can_partner_1"])
        payload = {
            "deck_name": "Needs Partner Deck Session",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr.name}' requires a Partner commander" in json_response["error"]


def test_fail_missing_required_ff(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        main_cmdr = _db.session.get(Commander, commanders["ff_1"])
        payload = {
            "deck_name": "Needs FF Deck Session",
            "deck_type": 7,
            "commander_id": commanders["ff_1"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr.name}' requires a Friends Forever commander" in json_response["error"]


def test_fail_missing_required_companion(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        main_cmdr = _db.session.get(Commander, commanders["doctor"])
        payload = {
            "deck_name": "Needs Companion Deck Session",
            "deck_type": 7,
            "commander_id": commanders["doctor"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr.name}' requires a Doctor's Companion commander" in json_response["error"]


def test_fail_missing_required_doctor(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        main_cmdr = _db.session.get(Commander, commanders["companion"])
        payload = {
            "deck_name": "Needs Doctor Deck Session",
            "deck_type": 7,
            "commander_id": commanders["companion"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr.name}' requires a Time Lord Doctor commander" in json_response["error"]


def test_fail_missing_required_background(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        main_cmdr = _db.session.get(Commander, commanders["needs_bg"])
        payload = {
            "deck_name": "Needs Background Deck Session",
            "deck_type": 7,
            "commander_id": commanders["needs_bg"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr.name}' requires a Background commander" in json_response["error"]


def test_fail_invalid_main_commander_for_partner(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        main_cmdr = _db.session.get(Commander, commanders["no_partner"])
        payload = {
            "deck_name": "Invalid Main For Partner Session",
            "deck_type": 7,
            "commander_id": commanders["no_partner"],
            "partner_id": commanders["can_partner_1"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr.name}' cannot be paired with the selected Partner" in json_response["error"]


def test_fail_invalid_associated_commander_for_partner(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        assoc_cmdr = _db.session.get(Commander, commanders["invalid_partner"])
        payload = {
            "deck_name": "Invalid Associated Partner Session",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"],
            "partner_id": commanders["invalid_partner"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{assoc_cmdr.name}' is not a valid Partner" in json_response["error"]


def test_fail_invalid_associated_commander_for_ff(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        assoc_cmdr = _db.session.get(Commander, commanders["invalid_ff"])
        payload = {
            "deck_name": "Invalid Associated FF Session",
            "deck_type": 7,
            "commander_id": commanders["ff_1"],
            "friends_forever_id": commanders["invalid_ff"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{assoc_cmdr.name}' is not a valid Friends Forever" in json_response["error"]


def test_fail_invalid_associated_commander_for_background(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        assoc_cmdr = _db.session.get(Commander, commanders["invalid_bg"])
        payload = {
            "deck_name": "Invalid Associated Background Session",
            "deck_type": 7,
            "commander_id": commanders["needs_bg"],
            "background_id": commanders["invalid_bg"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{assoc_cmdr.name}' is not a valid Background" in json_response["error"]


def test_fail_invalid_associated_commander_for_doctor(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        assoc_cmdr = _db.session.get(Commander, commanders["invalid_doctor"])
        payload = {
            "deck_name": "Invalid Associated Doctor Session",
            "deck_type": 7,
            "commander_id": commanders["companion"],
            "time_lord_doctor_id": commanders["invalid_doctor"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{assoc_cmdr.name}' is not a valid Time Lord Doctor" in json_response["error"]


def test_fail_invalid_associated_commander_for_companion(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        assoc_cmdr = _db.session.get(Commander, commanders["invalid_companion"])
        payload = {
            "deck_name": "Invalid Associated Companion Session",
            "deck_type": 7,
            "commander_id": commanders["doctor"],
            "doctor_companion_id": commanders["invalid_companion"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{assoc_cmdr.name}' is not a valid Doctor Companion" in json_response["error"]


def test_fail_commander_equals_partner(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "Same Commander Partner Session",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"],
            "partner_id": commanders["can_partner_1"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert "Commander and associated Commander cannot be the same" in json_response["error"]


def test_fail_multiple_associated_ids(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "Too Many Partners Session",
            "deck_type": 7,
            "commander_id": commanders["can_partner_1"],
            "partner_id": commanders["can_partner_2"],
            "friends_forever_id": commanders["ff_1"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert "Only one associated commander type" in json_response["error"]


def test_fail_deck_name_missing(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_type": 7,
            "commander_id": commanders["no_partner"]
        }
        response = client.post(
            "/api/register_deck",
            json=payload,
            headers={"X-CSRF-TOKEN": csrf_token}
        )
        json_response = response.get_json()

        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert "Add a Deck Name" in json_response["error"]


def test_fail_not_authenticated(client, app, commanders): 
    with app.app_context():
        with client.session_transaction() as sess:
            sess.clear()

        payload = {
            "deck_name": "Auth Test Deck Session",
            "deck_type": 7,
            "commander_id": commanders["no_partner"]
        }
        response = client.post("/api/register_deck", json=payload)

        assert response.status_code == 401
        json_response = response.get_json()
        assert json_response is not None and "msg" in json_response
        assert "Authentication required" in json_response["msg"]