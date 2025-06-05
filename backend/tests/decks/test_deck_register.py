# backend/tests/decks/test_deck_register.py

import pytest
from backend.models import User, Commander, Deck, DeckType, CommanderDeck
from flask_bcrypt import Bcrypt
from backend import db # Use pytest-flask-sqlalchemy 'db'
from sqlalchemy import select

COMMANDER_DECK_TYPE_ID = 7 # Define globally for tests

# --- Fixtures ---
@pytest.fixture(scope='function')
def test_user_deck_reg(app, db): # Renamed to avoid conflict if conftest.py has 'test_user'
    bcrypt = Bcrypt(app)
    # Using more unique names to avoid clashes if DB is not perfectly clean between test runs
    username = "deckreg_user_v7" 
    email = "deckreg_v7@example.com"
    first_name = "DeckRegV7"
    last_name = "UserV7"
    password = "password123v7"

    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == email.lower()))
        if not user: 
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(first_name=first_name, last_name=last_name, email=email.lower(), username=username, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user) # Ensure user.id is populated
        else: 
            # Ensure password is correct for login if user exists from a previous partial run
            if not bcrypt.check_password_hash(user.password_hash, password):
                 user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                 db.session.commit()
        yield {"user_obj": user, "password": password}


@pytest.fixture(scope='function')
def logged_in_client_deck_reg(client, test_user_deck_reg): # Use renamed fixture
    login_resp = client.post('/api/auth/login', json={
        'email': test_user_deck_reg["user_obj"].email,
        'password': test_user_deck_reg["password"]
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.get_data(as_text=True)}"
    csrf_resp = client.get('/api/auth/csrf_token')
    assert csrf_resp.status_code == 200
    csrf_token = csrf_resp.get_json().get('csrf_token')
    assert csrf_token is not None
    yield client, csrf_token


@pytest.fixture(scope='function')
def commanders_deck_reg(app, db): # Renamed fixture
    with app.app_context():
        commander_type_name = "Commander" 
        dt = db.session.get(DeckType, COMMANDER_DECK_TYPE_ID)
        if not dt:
            dt = DeckType(id=COMMANDER_DECK_TYPE_ID, name=commander_type_name)
            db.session.merge(dt)
            db.session.commit()

        # Using V7 in names/scryfall_ids for uniqueness
        cmdrs_data = {
            "no_partner": {"name": "Solo Cmdr RegTestV7", "scryfall_id": "solo_reg_v7"},
            "can_partner_1": {"name": "Partner Cmdr 1 RegTestV7", "scryfall_id": "p1_reg_v7", "partner": True},
            "can_partner_2": {"name": "Partner Cmdr 2 RegTestV7", "scryfall_id": "p2_reg_v7", "partner": True},
            "ff_1": {"name": "FF Cmdr 1 RegTestV7", "scryfall_id": "ff1_reg_v7", "friends_forever": True},
            "ff_2": {"name": "FF Cmdr 2 RegTestV7", "scryfall_id": "ff2_reg_v7", "friends_forever": True},
            "doctor": {"name": "The Doctor RegTestV7", "scryfall_id": "doc_reg_v7", "time_lord_doctor": True}, 
            "companion": {"name": "The Companion RegTestV7", "scryfall_id": "comp_reg_v7", "doctor_companion": True}, 
            "needs_bg": {"name": "Needs Background RegTestV7", "scryfall_id": "nbg_reg_v7", "choose_a_background": True},
            "is_bg": {"name": "Is Background RegTestV7", "scryfall_id": "bg_reg_v7", "background": True},
            "invalid_partner": {"name": "Not Partner RegTestV7", "scryfall_id": "invp_reg_v7"}, 
            "invalid_ff": {"name": "Not FF RegTestV7", "scryfall_id": "invff_reg_v7"},
            "invalid_bg": {"name": "Not BG RegTestV7", "scryfall_id": "invbg_reg_v7"},
        }
        cmdrs = {}
        default_abilities = {
            "partner": False, "friends_forever": False, "choose_a_background": False,
            "time_lord_doctor": False, "doctor_companion": False, "background": False
        }
        for key, data_item in cmdrs_data.items():
            # Ensure all boolean ability flags are present, defaulting to False
            full_data = {**default_abilities, **data_item}
            
            cmdr = db.session.scalar(select(Commander).where(Commander.scryfall_id == full_data['scryfall_id']))
            if not cmdr:
                cmdr = Commander(**full_data)
                db.session.add(cmdr)
            else: 
                changed = False
                for attr_key, attr_value in full_data.items():
                    if hasattr(cmdr, attr_key) and getattr(cmdr, attr_key) != attr_value:
                        setattr(cmdr, attr_key, attr_value)
                        changed = True
                if changed:
                    db.session.add(cmdr)
            cmdrs[key] = cmdr
        db.session.commit() 
        
        for cmdr_obj in cmdrs.values():
            if cmdr_obj.id is None: db.session.refresh(cmdr_obj)

        commander_ids = {k: c.id for k, c in cmdrs.items() if c.id is not None}
        if len(commander_ids) != len(cmdrs):
            missing_ids = [k for k, c in cmdrs.items() if c.id is None]
            pytest.fail(f"Failed to get IDs for commanders: {missing_ids}")
            
        yield commander_ids

# --- Tests ---

def test_register_simple_commander_success(app, db, logged_in_client_deck_reg, commanders_deck_reg, test_user_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    user_id = test_user_deck_reg["user_obj"].id # Get user_id from the fixture
    with app.app_context():
        payload = {
            "deck_name": "Simple Commander Deck Reg V7 Test", 
            "commander_id": commanders_deck_reg["no_partner"]
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()

        assert response.status_code == 201, f"API Error: {json_response.get('error', json_response.get('message', 'No error message'))}"
        assert json_response.get("message") == "Deck registered successfully"
        deck_resp = json_response.get("deck", {})
        assert deck_resp.get("name") == "Simple Commander Deck Reg V7 Test"
        assert deck_resp.get("commander_id") == commanders_deck_reg["no_partner"]
        assert deck_resp.get("partner_id") is None 
        assert deck_resp.get("deck_type_id") == COMMANDER_DECK_TYPE_ID

        deck_db = db.session.scalar(select(Deck).where(Deck.name == "Simple Commander Deck Reg V7 Test", Deck.user_id == user_id))
        assert deck_db is not None
        assert deck_db.deck_type_id == COMMANDER_DECK_TYPE_ID
        cmd_deck_db = db.session.scalar(select(CommanderDeck).where(CommanderDeck.deck_id == deck_db.id))
        assert cmd_deck_db is not None
        assert cmd_deck_db.commander_id == commanders_deck_reg["no_partner"]
        assert cmd_deck_db.associated_commander_id is None

def test_register_valid_partner_success(app, db, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    with app.app_context():
        payload = {
            "deck_name": "Partner Power Reg V7", 
            "commander_id": commanders_deck_reg["can_partner_1"],
            "partner_id": commanders_deck_reg["can_partner_2"] 
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()
        assert response.status_code == 201, f"API Error: {json_response.get('error', json_response.get('message'))}"
        deck_resp = json_response.get("deck", {})
        assert deck_resp.get("deck_type_id") == COMMANDER_DECK_TYPE_ID
        assert deck_resp.get("commander_id") == commanders_deck_reg["can_partner_1"]
        assert deck_resp.get("partner_id") == commanders_deck_reg["can_partner_2"]

def test_register_valid_ff_success(app, db, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    payload = {
        "deck_name": "BFF Deck Reg V7",
        "commander_id": commanders_deck_reg["ff_1"],
        "friends_forever_id": commanders_deck_reg["ff_2"]
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 201, f"API Error: {json_response.get('error', json_response.get('message'))}"
    deck_resp = json_response.get("deck", {})
    assert deck_resp.get("deck_type_id") == COMMANDER_DECK_TYPE_ID
    assert deck_resp.get("commander_id") == commanders_deck_reg["ff_1"]
    assert deck_resp.get("friends_forever_id") == commanders_deck_reg["ff_2"]


def test_register_valid_doctor_companion_success(app, db, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    payload = {
        "deck_name": "TARDIS Crew Reg V7",
        "commander_id": commanders_deck_reg["doctor"], 
        "doctor_companion_id": commanders_deck_reg["companion"]
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 201, f"API Error: {json_response.get('error', json_response.get('message'))}"
    deck_resp = json_response.get("deck", {})
    assert deck_resp.get("deck_type_id") == COMMANDER_DECK_TYPE_ID
    assert deck_resp.get("commander_id") == commanders_deck_reg["doctor"]
    assert deck_resp.get("doctor_companion_id") == commanders_deck_reg["companion"]


def test_register_valid_choose_background_success(app, db, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    payload = {
        "deck_name": "Background Story Reg V7",
        "commander_id": commanders_deck_reg["needs_bg"],
        "background_id": commanders_deck_reg["is_bg"]
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 201, f"API Error: {json_response.get('error', json_response.get('message'))}"
    deck_resp = json_response.get("deck", {})
    assert deck_resp.get("deck_type_id") == COMMANDER_DECK_TYPE_ID
    assert deck_resp.get("commander_id") == commanders_deck_reg["needs_bg"]
    assert deck_resp.get("background_id") == commanders_deck_reg["is_bg"]


# --- Failure Cases ---
def test_fail_missing_deck_name(app, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    payload = {
        # "deck_name": "Missing Name Test", # Name is missing
        "commander_id": commanders_deck_reg["no_partner"]
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 400
    assert json_response is not None and "error" in json_response
    assert "Deck Name is required." == json_response["error"]

def test_fail_missing_commander_id(app, logged_in_client_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    payload = {"deck_name": "No Commander Deck Reg V7"}
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 400
    assert json_response is not None and "error" in json_response
    # This assertion should now pass if the backend route's first check is for commander_id
    assert "A Commander is required." == json_response["error"] 

def test_fail_missing_required_partner(app, db, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    with app.app_context(): 
        main_cmdr_obj = db.session.get(Commander, commanders_deck_reg["can_partner_1"])
        assert main_cmdr_obj is not None
        payload = {
            "deck_name": "Needs Partner Deck Reg V7",
            "commander_id": commanders_deck_reg["can_partner_1"]
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()
        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr_obj.name}' requires a Partner commander." == json_response["error"]

def test_fail_invalid_partner(app, db, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    with app.app_context():
        invalid_partner_obj = db.session.get(Commander, commanders_deck_reg["invalid_partner"])
        assert invalid_partner_obj is not None
        payload = {
            "deck_name": "Invalid Partner Deck Reg V7",
            "commander_id": commanders_deck_reg["can_partner_1"],
            "partner_id": commanders_deck_reg["invalid_partner"]
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()
        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{invalid_partner_obj.name}' is not a valid Partner." == json_response["error"]


def test_fail_not_authenticated(client, app, commanders_deck_reg): # Use renamed commanders fixture
    with app.app_context():
        with client.session_transaction() as sess:
            sess.clear()
        payload = {
            "deck_name": "Auth Test Deck Reg V7",
            "commander_id": commanders_deck_reg["no_partner"]
        }
        response = client.post("/api/register_deck", json=payload) 
        assert response.status_code == 401
        json_response = response.get_json()
        assert json_response is not None and "msg" in json_response 
        assert "Authentication required" in json_response["msg"]

def test_fail_multiple_associated_commanders(app, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    payload = {
        "deck_name": "Too Many Partners Reg V7",
        "commander_id": commanders_deck_reg["can_partner_1"],
        "partner_id": commanders_deck_reg["can_partner_2"],
        "friends_forever_id": commanders_deck_reg["ff_1"] # Adding a second type of association
    }
    response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
    json_response = response.get_json()
    assert response.status_code == 400
    assert json_response is not None and "error" in json_response
    assert "Only one associated commander type can be provided." == json_response["error"]

def test_fail_commander_cannot_pair_with_provided_type(app, db, logged_in_client_deck_reg, commanders_deck_reg):
    client, csrf_token = logged_in_client_deck_reg
    with app.app_context():
        main_cmdr_obj = db.session.get(Commander, commanders_deck_reg["no_partner"]) # This commander has no pairing abilities
        assert main_cmdr_obj is not None
        payload = {
            "deck_name": "Mismatched Pair Reg V7",
            "commander_id": commanders_deck_reg["no_partner"],
            "partner_id": commanders_deck_reg["can_partner_1"] # Trying to add a partner
        }
        response = client.post("/api/register_deck", json=payload, headers={"X-CSRF-TOKEN": csrf_token})
        json_response = response.get_json()
        assert response.status_code == 400
        assert json_response is not None and "error" in json_response
        assert f"'{main_cmdr_obj.name}' cannot be paired with the selected Partner." == json_response["error"]