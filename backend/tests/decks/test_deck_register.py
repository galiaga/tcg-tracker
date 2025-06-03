# backend/tests/decks/test_deck_register.py

import pytest
from backend.models import User, Commander, Deck, DeckType, UserDeck, CommanderDeck
from flask_bcrypt import Bcrypt
from backend import db as _db
from sqlalchemy import select

# --- Fixtures (Assuming these are correctly set up as per your last version) ---
@pytest.fixture(scope='function')
def test_user(app):
    bcrypt = Bcrypt(app)
    username = "deckreg_testuser_v4_final" # Unique name
    email = "deckreg_v4_final@example.com"
    first_name = "DeckRegV4Final"
    last_name = "UserV4Final"
    password = "password123v4final"

    with app.app_context():
        user = _db.session.scalar(select(User).where(User.email == email.lower()))
        if not user: # Simplified creation if not found
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(first_name=first_name, last_name=last_name, email=email.lower(), username=username, password_hash=hashed_password)
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        else: # Ensure password is correct for login if user exists
            if not bcrypt.check_password_hash(user.password_hash, password):
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 _db.session.commit()
        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def logged_in_client(client, test_user):
    login_resp = client.post('/api/auth/login', json={
        'email': test_user["user_obj"].email,
        'password': test_user["password"]
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.get_data(as_text=True)}"
    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200
    csrf_token = csrf_resp.get_json().get('csrf_token')
    assert csrf_token is not None
    yield client, csrf_token


@pytest.fixture(scope='function')
def commanders(app, db):
    with app.app_context():
        commander_type_id = 7
        commander_type_name = "Commander"
        dt = db.session.get(DeckType, commander_type_id)
        if not dt:
            dt = DeckType(id=commander_type_id, name=commander_type_name)
            db.session.merge(dt)
        db.session.commit()

        cmdrs_data = {
            "no_partner": {"name": "Solo Cmdr RegTestV4", "scryfall_id": "solo1_reg_v4", "partner": False, "friends_forever": False, "choose_a_background": False, "time_lord_doctor": False, "doctor_companion": False, "background": False},
            "can_partner_1": {"name": "Partner Cmdr 1 RegTestV4", "scryfall_id": "p1_reg_v4", "partner": True},
            "can_partner_2": {"name": "Partner Cmdr 2 RegTestV4", "scryfall_id": "p2_reg_v4", "partner": True},
            "ff_1": {"name": "FF Cmdr 1 RegTestV4", "scryfall_id": "ff1_reg_v4", "friends_forever": True},
            "ff_2": {"name": "FF Cmdr 2 RegTestV4", "scryfall_id": "ff2_reg_v4", "friends_forever": True},
            "doctor": {"name": "The Doctor RegTestV4", "scryfall_id": "doc1_reg_v4", "time_lord_doctor": True}, # This commander IS a Doctor
            "companion": {"name": "The Companion RegTestV4", "scryfall_id": "comp1_reg_v4", "doctor_companion": True}, # This commander IS a Companion
            "needs_bg": {"name": "Needs Background RegTestV4", "scryfall_id": "nbg1_reg_v4", "choose_a_background": True},
            "is_bg": {"name": "Is Background RegTestV4", "scryfall_id": "bg1_reg_v4", "background": True},
            "invalid_partner": {"name": "Not Partner RegTestV4", "scryfall_id": "invp1_reg_v4"}, # Defaults to False for abilities
            "invalid_ff": {"name": "Not FF RegTestV4", "scryfall_id": "invff1_reg_v4"},
            "invalid_bg": {"name": "Not BG RegTestV4", "scryfall_id": "invbg1_reg_v4"},
            "invalid_doctor": {"name": "Not Doctor RegTestV4", "scryfall_id": "invdoc1_reg_v4"},
            "invalid_companion": {"name": "Not Companion RegTestV4", "scryfall_id": "invcomp1_reg_v4"}
        }
        cmdrs = {}
        for key, data_item in cmdrs_data.items():
            full_data = {
                "name": data_item["name"], "scryfall_id": data_item["scryfall_id"],
                "partner": data_item.get("partner", False), "friends_forever": data_item.get("friends_forever", False),
                "choose_a_background": data_item.get("choose_a_background", False),
                "time_lord_doctor": data_item.get("time_lord_doctor", False), "doctor_companion": data_item.get("doctor_companion", False),
                "background": data_item.get("background", False)
            }
            cmdr = db.session.scalar(select(Commander).where(Commander.scryfall_id == full_data['scryfall_id']))
            if not cmdr:
                cmdr = Commander(**full_data)
                db.session.add(cmdr)
            cmdrs[key] = cmdr
        db.session.commit()
        commander_ids = {k: c.id for k, c in cmdrs.items()}
        yield commander_ids

# --- Tests ---

def test_register_simple_commander_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "Simple Commander Deck Reg V4",
            "commander_id": commanders["no_partner"]
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()

        assert response.status_code == 201, f"API Error: {json_response.get('error')}"
        assert json_response["message"] == "Deck registered successfully"
        deck_resp = json_response["deck"]
        assert deck_resp["name"] == "Simple Commander Deck Reg V4"
        assert deck_resp["commander_id"] == commanders["no_partner"]
        assert deck_resp.get("partner_id") is None # Use .get() for optional keys
        assert deck_resp.get("friends_forever_id") is None
        assert deck_resp.get("doctor_companion_id") is None
        assert deck_resp.get("time_lord_doctor_id") is None
        assert deck_resp.get("background_id") is None
        assert deck_resp["deck_type_id"] == 7

        deck_db = _db.session.scalar(select(Deck).where(Deck.name == "Simple Commander Deck Reg V4"))
        assert deck_db is not None
        assert deck_db.deck_type_id == 7
        cmd_deck_db = _db.session.scalar(select(CommanderDeck).where(CommanderDeck.deck_id == deck_db.id))
        assert cmd_deck_db is not None
        assert cmd_deck_db.commander_id == commanders["no_partner"]
        assert cmd_deck_db.associated_commander_id is None

def test_register_valid_partner_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context():
        payload = {
            "deck_name": "Partner Power Reg V4",
            "commander_id": commanders["can_partner_1"],
            "partner_id": commanders["can_partner_2"]
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()
        assert response.status_code == 201, f"API Error: {json_response.get('error')}"
        deck_resp = json_response["deck"]
        assert deck_resp["deck_type_id"] == 7
        assert deck_resp["commander_id"] == commanders["can_partner_1"]
        assert deck_resp["partner_id"] == commanders["can_partner_2"]

# ... (Similar success tests for ff, doctor_companion, choose_background - ensure they check for specific assoc_key_id)

def test_register_valid_ff_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    payload = {
        "deck_name": "BFF Deck Reg V4",
        "commander_id": commanders["ff_1"],
        "friends_forever_id": commanders["ff_2"]
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 201, f"API Error: {json_response.get('error')}"
    deck_resp = json_response["deck"]
    assert deck_resp["deck_type_id"] == 7
    assert deck_resp["commander_id"] == commanders["ff_1"]
    assert deck_resp["friends_forever_id"] == commanders["ff_2"]


def test_register_valid_doctor_companion_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    payload = {
        "deck_name": "TARDIS Crew Reg V4",
        "commander_id": commanders["doctor"], # Main commander is "The Doctor"
        "doctor_companion_id": commanders["companion"] # Associated is "The Companion"
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 201, f"API Error: {json_response.get('error')}"
    deck_resp = json_response["deck"]
    assert deck_resp["deck_type_id"] == 7
    assert deck_resp["commander_id"] == commanders["doctor"]
    assert deck_resp["doctor_companion_id"] == commanders["companion"]


def test_register_valid_choose_background_success(app, db, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    payload = {
        "deck_name": "Background Story Reg V4",
        "commander_id": commanders["needs_bg"],
        "background_id": commanders["is_bg"]
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 201, f"API Error: {json_response.get('error')}"
    deck_resp = json_response["deck"]
    assert deck_resp["deck_type_id"] == 7
    assert deck_resp["commander_id"] == commanders["needs_bg"]
    assert deck_resp["background_id"] == commanders["is_bg"]


# --- Failure Cases ---
def test_fail_missing_commander_id(app, logged_in_client):
    client, csrf_token = logged_in_client
    payload = {"deck_name": "No Commander Deck Reg V4"}
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 400
    assert json_response is not None and "error" in json_response
    assert "A Commander is required." == json_response["error"] # Exact match

def test_fail_missing_required_partner(app, logged_in_client, commanders):
    client, csrf_token = logged_in_client
    with app.app_context(): # Ensure session for db.session.get
        main_cmdr = _db.session.get(Commander, commanders["can_partner_1"])
        assert main_cmdr is not None, "Test setup error: can_partner_1 commander not found"
        payload = {
            "deck_name": "Needs Partner Deck Reg V4",
            "commander_id": commanders["can_partner_1"]
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()
        assert response.status_code == 400, f"API returned {response.status_code} instead of 400. Response: {json_response}"
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr.name}' requires a Partner commander." == json_response["error"]


# ... (All other failure cases should be reviewed to ensure the expected error messages
#      match what the updated backend /api/register_deck route now returns for those specific scenarios)

def test_fail_not_authenticated(client, app, commanders):
    with app.app_context():
        with client.session_transaction() as sess:
            sess.clear()
        payload = {
            "deck_name": "Auth Test Deck Reg V4",
            "commander_id": commanders["no_partner"]
        }
        response = client.post("/api/register_deck", json=payload)
        assert response.status_code == 401
        json_response = response.get_json()
        assert json_response is not None and "msg" in json_response
        assert "Authentication required" in json_response["msg"]