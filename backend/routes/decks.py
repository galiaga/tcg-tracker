from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.models import CommanderDeck, Commander, UserDeck, Deck
from backend.services.matches.match_service import get_deck_stats, get_all_decks_stats
from backend.services.decks.get_user_decks_service import get_user_decks
from backend.services.decks.get_commander_attributes_service import get_commander_attributes_by_id
import json
import logging

decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")

COMMANDER_DECK_TYPE_ID = 7

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first_or_404(
        description=f"Deck with id {deck_id} not found for this user."
    )
    deck_data = deck.to_dict()

    stats = get_deck_stats(user_id, deck_id)
    if stats:
        deck_data.update({
            "win_rate": stats.get("win_rate", 0),
            "total_matches": stats.get("total_matches", 0),
            "total_wins": stats.get("total_wins", 0)
        })
    else:
         deck_data.update({
            "win_rate": 0,
            "total_matches": 0,
            "total_wins": 0
        })

    if deck_data.get("deck_type", {}).get("id") == COMMANDER_DECK_TYPE_ID:
        commander_deck_info = CommanderDeck.query.filter_by(deck_id=deck.id).first()
        if commander_deck_info:
            if commander_deck_info.commander_id:
                commander_attributes = get_commander_attributes_by_id(commander_deck_info.commander_id)
                if commander_attributes:
                    deck_data["commander_name"] = commander_attributes.get("name")
                    deck_data["commander_id"] = commander_deck_info.commander_id

            if commander_deck_info.associated_commander_id:
                associated_commander_attributes = get_commander_attributes_by_id(commander_deck_info.associated_commander_id)
                if associated_commander_attributes:
                    deck_data["associated_commander_name"] = associated_commander_attributes.get("name")
                    deck_data["associated_commander_id"] = commander_deck_info.associated_commander_id

    return jsonify(deck_data), 200


@decks_bp.route("/register_deck", methods=["POST"])
@jwt_required()
def register_deck():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    deck_name = data.get("deck_name")
    deck_type_id_str = data.get("deck_type")

    if not deck_name:
        return jsonify({"error": "Add a Deck Name"}), 400
    if not deck_type_id_str:
        return jsonify({"error": "Deck type is required"}), 400

    try:
        deck_type_id = int(deck_type_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid Deck Type ID"}), 400

    commander_id = data.get("commander_id")
    partner_id = data.get("partner_id")
    friends_forever_id = data.get("friends_forever_id")
    doctor_companion_id = data.get("doctor_companion_id")
    time_lord_doctor_id = data.get("time_lord_doctor_id")
    background_id = data.get("background_id")

    if deck_type_id == COMMANDER_DECK_TYPE_ID and not commander_id:
        return jsonify({"error": "Add your Commander"}), 400

    commander = None
    if commander_id:
        try:
            commander_id = int(commander_id)
            commander = db.session.get(Commander, commander_id)
            if not commander:
                 return jsonify({"error": "Selected Commander not found."}), 404
        except (ValueError, TypeError):
             return jsonify({"error": "Invalid Commander ID format."}), 400

    try:
        new_deck = Deck(user_id=user_id, name=deck_name, deck_type_id=deck_type_id)
        db.session.add(new_deck)
        db.session.flush()

        user_deck = UserDeck(user_id=user_id, deck_id=new_deck.id)
        db.session.add(user_deck)

        if deck_type_id == COMMANDER_DECK_TYPE_ID and commander_id:
            associations = {
                "partner_id": partner_id,
                "friends_forever_id": friends_forever_id,
                "time_lord_doctor_id": time_lord_doctor_id,
                "doctor_companion_id": doctor_companion_id,
                "background_id": background_id
            }

            non_null_associations = {}
            for key, value in associations.items():
                if value is not None:
                    try:
                        non_null_associations[key] = int(value)
                    except (ValueError, TypeError):
                         db.session.rollback()
                         return jsonify({"error": f"Invalid ID format for {key}."}), 400

            if len(non_null_associations) > 1:
                db.session.rollback()
                return jsonify({
                    "error": "Only one associated commander type (Partner, Friends Forever, Doctor's Companion, Time Lord Doctor, or Background) can be included."
                }), 400

            associated_commander_id = next(iter(non_null_associations.values()), None)
            assoc_key = next(iter(non_null_associations.keys()), None)

            if associated_commander_id:
                if commander_id == associated_commander_id:
                    db.session.rollback()
                    return jsonify({"error": "Commander and associated Commander cannot be the same."}), 400

                associated_commander = db.session.get(Commander, associated_commander_id)
                if not associated_commander:
                    db.session.rollback()
                    return jsonify({"error": "Associated Commander not found."}), 404

                ASSOCIATION_VALIDATION_RULES = {
                    "partner_id": lambda assoc: assoc.partner,
                    "friends_forever_id": lambda assoc: assoc.friends_forever,
                    "time_lord_doctor_id": lambda assoc: assoc.time_lord_doctor,
                    "doctor_companion_id": lambda assoc: assoc.doctor_companion,
                    "background_id": lambda assoc: assoc.background,
                }

                MAIN_COMMANDER_REQUIREMENTS = {
                    "partner_id": lambda main: main.partner,
                    "friends_forever_id": lambda main: main.friends_forever,
                    "time_lord_doctor_id": lambda main: main.doctor_companion,
                    "doctor_companion_id": lambda main: main.time_lord_doctor,
                    "background_id": lambda main: main.choose_a_background,
                }

                assoc_validator = ASSOCIATION_VALIDATION_RULES.get(assoc_key)
                main_req_validator = MAIN_COMMANDER_REQUIREMENTS.get(assoc_key)
                label = assoc_key.replace("_id", "").replace("_", " ").title()

                if not assoc_validator or not assoc_validator(associated_commander):
                    db.session.rollback()
                    return jsonify({"error": f"'{associated_commander.name}' is not a valid {label}."}), 400

                if not main_req_validator or not main_req_validator(commander):
                    if assoc_key == "background_id":
                        error_msg = f"'{commander.name}' does not have the 'Choose a Background' ability required for a Background commander."
                    else:
                        error_msg = f"'{commander.name}' cannot be paired with the selected {label}."
                    db.session.rollback()
                    return jsonify({"error": error_msg}), 400

                commander_deck = CommanderDeck(
                    deck_id=new_deck.id,
                    commander_id=commander_id,
                    associated_commander_id=associated_commander_id
                )
                db.session.add(commander_deck)

            else:
                if commander.partner or commander.friends_forever or commander.choose_a_background or commander.time_lord_doctor or commander.doctor_companion:
                    required_partner_type = ""
                    if commander.partner: required_partner_type = "Partner"
                    elif commander.friends_forever: required_partner_type = "Friends Forever"
                    elif commander.choose_a_background: required_partner_type = "Background"
                    elif commander.time_lord_doctor: required_partner_type = "Doctor's Companion"
                    elif commander.doctor_companion: required_partner_type = "Time Lord Doctor"

                    if required_partner_type:
                        db.session.rollback()
                        return jsonify({"error": f"'{commander.name}' requires a {required_partner_type} commander."}), 400

                commander_deck = CommanderDeck(
                    deck_id=new_deck.id,
                    commander_id=commander_id,
                    associated_commander_id=None
                )
                db.session.add(commander_deck)

        db.session.commit()

        response_data = {
            "message": "Deck registered successfully",
            "deck": {
                "id": new_deck.id,
                "name": new_deck.name,
                "deck_type": new_deck.deck_type_id,
                "commander_id": None,
                "partner_id": None,
                "friends_forever_id": None,
                "doctor_companion_id": None,
                "time_lord_doctor_id": None,
                "background_id": None
            }
        }
        if deck_type_id == COMMANDER_DECK_TYPE_ID and 'commander_deck' in locals():
             response_data["deck"]["commander_id"] = commander_deck.commander_id
             if commander_deck.associated_commander_id:
                 saved_assoc_key = next((k for k, v in non_null_associations.items() if v == commander_deck.associated_commander_id), None)
                 if saved_assoc_key:
                     response_data["deck"][saved_assoc_key] = commander_deck.associated_commander_id

        return Response(
            json.dumps(response_data, indent=4),
            mimetype="application/json",
            status=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck registration: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "details": str(e)}), 500

@decks_bp.route("/user_decks", methods=["GET"])
@jwt_required()
def user_decks():
    user_id = get_jwt_identity()
    deck_type_filter = request.args.get('deck_type_id', default=None)

    try:
        user_decks_result = get_user_decks(user_id, deck_type_id=deck_type_filter)

        if not user_decks_result:
            return jsonify([]), 200

        all_stats = get_all_decks_stats(user_id)
        stats_map = {deck_stat["id"]: deck_stat for deck_stat in all_stats}

        decks_list = []
        for deck, deck_type in user_decks_result:
            deck_stats = stats_map.get(deck.id, {})
            decks_list.append({
                "id": deck.id,
                "creation_date": deck.creation_date,
                "name": deck.name,
                "type": deck.deck_type_id,
                "deck_type": {
                    "id": deck_type.id,
                    "name": deck_type.name
                },
                "win_rate": deck_stats.get("win_rate", 0),
                "total_matches": deck_stats.get("total_matches", 0),
                "total_wins": deck_stats.get("total_wins", 0),
                "last_match": deck_stats.get("last_match", None)
            })

        return jsonify(decks_list), 200

    except Exception as e:
         logger.error(f"Error fetching user decks: {e}", exc_info=True)
         return jsonify({"error": "Failed to fetch user decks"}), 500


@decks_bp.route("/decks/<int:deck_id>", methods=["PATCH"])
@jwt_required()
def update_deck(deck_id):
    user_id = get_jwt_identity()
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first_or_404(
         description=f"Deck with id {deck_id} not found for this user."
    )

    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400

    updated = False
    if 'deck_name' in data:
        new_name = data['deck_name'].strip()
        if not new_name:
            return jsonify({"error": "Deck Name cannot be empty"}), 400
        if deck.name != new_name:
            deck.name = new_name
            updated = True

    if not updated:
         return jsonify({"message": "No changes detected"}), 200

    try:
        db.session.commit()
        updated_deck_data = deck.to_dict()
        return jsonify({
            "message": "Deck updated successfully",
            "deck": updated_deck_data
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck update: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e)}), 500


@decks_bp.route("/decks/<int:deck_id>", methods=["DELETE"])
@jwt_required()
def delete_deck(deck_id):
    user_id = get_jwt_identity()
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first_or_404(
        description=f"Deck with id {deck_id} not found for this user."
    )

    try:
        CommanderDeck.query.filter_by(deck_id=deck.id).delete()
        UserDeck.query.filter_by(deck_id=deck.id, user_id=user_id).delete()

        db.session.delete(deck)
        db.session.commit()

        logger.info(f"Deck {deck_id} deleted successfully by user {user_id}")
        return jsonify({"message": f"Deck {deck_id} deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck deletion: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e)}), 500