from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend import db
from backend.models.deck import Deck
from backend.models.user_deck import UserDeck
from backend.models.commander_deck import CommanderDeck
from backend.services.matches.match_service import get_deck_stats
from backend.services.matches.match_service import get_all_decks_stats
from backend.services.decks.get_user_decks_service import get_user_decks

import json

decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")

COMMANDER_DECK_TYPE_ID = 7

@decks_bp.route("/decks", methods=["GET"])
@jwt_required()
def get_all_decks():
    decks = Deck.query.all()
    decks_list = [{"id": deck.id, "deck_name": deck.name} for deck in decks]
    return jsonify(decks_list)

@decks_bp.route("/decks/<int:deck_id>", methods=["GET"])
@jwt_required()
def deck_details(deck_id):
    user_id = get_jwt_identity()
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first_or_404()
    deck_data = deck.to_dict()

    stats = get_deck_stats(user_id, deck_id)
    if stats:
        deck_data.update({
            "win_rate": stats["win_rate"],
            "total_matches": stats["total_matches"],
            "total_wins": stats["total_wins"]
        })
    return jsonify(deck_data), 200

@decks_bp.route("/register_deck", methods=["POST"])
@jwt_required()
def register_deck():
    if request.method == "GET":
        return jsonify({"error": "This endpoint only supports POST requests"}), 405

    user_id = get_jwt_identity()
    data = request.get_json()
    deck_name = data.get("deck_name")
    deck_type_id = data.get("deck_type")

    try:
        deck_type_id = int(deck_type_id)
    except ValueError:
        pass

    commander_id = data.get("commander_id")
    partner_id = data.get("partner_id")
    friends_forever_id = data.get("friends_forever_id")
    doctor_companion_id = data.get("doctor_companion_id")
    time_lord_doctor_id = data.get("time_lord_doctor_id")
    background_id = data.get("background_id")

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    if not deck_name:
        return jsonify({"error": "Add a Deck Name"}), 400
    if (deck_type_id == COMMANDER_DECK_TYPE_ID) and not commander_id:
        return jsonify({"error": "Add your Commander"}), 400
    
    from backend.models import Commander
    commander = db.session.get(Commander, commander_id)

    if commander and commander.partner and not partner_id:
        return jsonify({"error": "This Commander requires a Partner."}), 400
    
    if commander and commander.friends_forever and not friends_forever_id:
        return jsonify({"error": "This Commander requires another Friend Forever Commander."}), 400
    
    if commander and commander.doctor_companion and not time_lord_doctor_id:
        return jsonify({"error": "This Doctor's Companion requires a Time Lord Doctor Commander."}), 400
    
    if commander and commander.time_lord_doctor and not doctor_companion_id:
        return jsonify({"error": "This Doctor requires a Doctor's Companion Commander."}), 400
    
    try:
        new_deck = Deck(user_id=user_id, name=deck_name, deck_type_id=deck_type_id)
        db.session.add(new_deck)
        db.session.commit()

        user_deck = UserDeck(user_id=user_id, deck_id=new_deck.id)
        db.session.add(user_deck)

        associations = {
            "partner_id": partner_id,
            "friends_forever_id": friends_forever_id,
            "time_lord_doctor_id": time_lord_doctor_id,
            "doctor_companion_id": doctor_companion_id,
            "background_id": background_id
        }

        non_null_associations = {key: value for key, value in associations.items() if value is not None}

        if len(non_null_associations) > 1:
            return jsonify({
                "error": "Only one of partner_id, friends_forever_id, doctor_companion_id, time_lord_doctor_id or background_id can be included."
            }), 400
        
        if commander_id:
            associated_commander_id = next(iter(non_null_associations.values()), None)

            if associated_commander_id and str(commander_id) == str(associated_commander_id):
                return jsonify({"error": "Commander and associated Commander cannot be the same."}), 400
            
            VALIDATION_RULES = {
                "partner_id": lambda c: c.partner,
                "friends_forever_id": lambda c: c.friends_forever,
                "time_lord_doctor_id": lambda c: c.time_lord_doctor,
                "doctor_companion_id": lambda c: c.doctor_companion,
                "background_id": lambda c: c.background,
            }

            if associated_commander_id:
                assoc_key = next(iter(non_null_associations))
                associated_commander = db.session.get(Commander, associated_commander_id)

                if not associated_commander:
                    return jsonify({"error": "Associated Commander not found."}), 404

                if not VALIDATION_RULES[assoc_key](associated_commander):
                    label = assoc_key.replace("_id", "").replace("_", " ").title()
                    return jsonify({"error": f"{associated_commander.name} is not a valid {label}."}), 400
                
                REQUIRED_MAIN_TYPE = {
                    "partner_id": lambda c: c.partner,
                    "friends_forever_id": lambda c: c.friends_forever,
                    "time_lord_doctor_id": lambda c: c.doctor_companion,
                    "doctor_companion_id": lambda c: c.time_lord_doctor,
                    "background_id": lambda c: c.choose_a_background,
                }

                required_main_validator = REQUIRED_MAIN_TYPE.get(assoc_key)
                if required_main_validator and not required_main_validator(commander):
                    label = assoc_key.replace("_id", "").replace("_", " ").title()
                    return jsonify({
                        "error": f"{commander.name} is not a valid main commander for associated {label}."
                    }), 400
                
                commander = db.session.get(Commander, commander_id)
                if not commander:
                    return jsonify({"error": "Commander not found."}), 404

            commander_deck = CommanderDeck(
                deck_id=new_deck.id,
                commander_id=commander_id,
                associated_commander_id=associated_commander_id
            )
            db.session.add(commander_deck)

        db.session.commit()

        return Response(
            json.dumps({
                "message": "Deck registered successfully",
                "deck": {
                    "id": new_deck.id,
                    "name": new_deck.name,
                    "deck_type": deck_type_id,
                    "commander_id": commander_id,
                    "partner_id": partner_id,
                    "friends_forever_id": friends_forever_id,
                    "doctor_companion_id": doctor_companion_id,
                    "time_lord_doctor_id": time_lord_doctor_id,
                    "background_id": background_id
                }
            }, indent=4),
            mimetype="application/json",
            status=201
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ Database error: {e}") 
        return jsonify({"error": "Database error", "details": str(e)}), 500
    
@decks_bp.route("/user_decks", methods=["GET"])
@jwt_required()
def user_decks():
    user_id = get_jwt_identity()
    user_decks = get_user_decks(user_id)

    if not user_decks:
        return jsonify([]), 200
    
    stats = {deck["id"]: deck for deck in get_all_decks_stats(user_id)}

    decks_list = [
        {
                "id": deck.id,
                "name": deck.name,
                "type": deck.deck_type_id,
            "deck_type": {
                "name": deck_type.name
            },
            "win_rate": stats.get(deck.id, {}).get("win_rate", 0),
            "total_matches": stats.get(deck.id, {}).get("total_matches", 0),
            "total_wins": stats.get(deck.id, {}).get("total_wins", 0),
            "last_match": stats.get(deck.id, {}).get("last_match", 0)

        } 
        for deck, deck_type in user_decks
    ]

    print(f"stats = {stats}")
    print(f"decks_list = {decks_list}")

    return jsonify(decks_list), 200