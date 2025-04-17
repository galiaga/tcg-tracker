from flask import Blueprint, jsonify, request, Response, session
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError
import json
import logging

from backend import db
from backend.models import CommanderDeck, Commander, UserDeck, Deck, Tag
from backend.services.matches.match_service import get_deck_stats, get_all_decks_stats
from backend.services.decks.get_user_decks_service import get_user_decks
from backend.services.decks.get_commander_attributes_service import get_commander_attributes_by_id
from backend.utils.decorators import login_required


decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")

COMMANDER_DECK_TYPE_ID = 7

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@decks_bp.route("/decks", methods=["GET"])
@login_required
def get_all_decks():
    # Note: Consider if this should be user-specific or if it's for admin purposes.
    # For user-specific decks, see /user_decks endpoint.
    stmt = select(Deck)
    decks = db.session.scalars(stmt).all()
    decks_list = [{"id": deck.id, "deck_name": deck.name} for deck in decks]
    return jsonify(decks_list)

@decks_bp.route("/decks/<int:deck_id>", methods=["GET"])
@login_required
def deck_details(deck_id):
    user_id = session.get('user_id')

    deck = db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
    if not deck or deck.user_id != user_id:
        return jsonify({"error": f"Deck with id {deck_id} not found for this user."}), 404

    deck_data = deck.to_dict() # Assuming Deck model has a suitable to_dict method

    stats = get_deck_stats(user_id, deck_id)
    deck_data.update({
        "win_rate": stats.get("win_rate", 0) if stats else 0,
        "total_matches": stats.get("total_matches", 0) if stats else 0,
        "total_wins": stats.get("total_wins", 0) if stats else 0
    })

    if deck_data.get("deck_type", {}).get("id") == COMMANDER_DECK_TYPE_ID:
        stmt_cd = select(CommanderDeck).where(CommanderDeck.deck_id == deck.id)
        commander_deck_info = db.session.scalars(stmt_cd).first()
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

    deck_data["tags"] = [{"id": tag.id, "name": tag.name} for tag in deck.tags]

    return jsonify(deck_data), 200

@decks_bp.route("/register_deck", methods=["POST"])
@login_required
def register_deck():
    user_id = session.get('user_id')
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

    commander_id_str = data.get("commander_id")
    partner_id_str = data.get("partner_id")
    friends_forever_id_str = data.get("friends_forever_id")
    doctor_companion_id_str = data.get("doctor_companion_id")
    time_lord_doctor_id_str = data.get("time_lord_doctor_id")
    background_id_str = data.get("background_id")

    commander_id = None
    commander = None
    if commander_id_str:
        try:
            commander_id = int(commander_id_str)
            commander = db.session.get(Commander, commander_id)
            if not commander:
                 return jsonify({"error": "Selected Commander not found."}), 404
        except (ValueError, TypeError):
             return jsonify({"error": "Invalid Commander ID format."}), 400

    if deck_type_id == COMMANDER_DECK_TYPE_ID and not commander_id:
        return jsonify({"error": "Add your Commander"}), 400

    try:
        new_deck = Deck(user_id=user_id, name=deck_name, deck_type_id=deck_type_id)
        db.session.add(new_deck)
        db.session.flush()

        user_deck = UserDeck(user_id=user_id, deck_id=new_deck.id)
        db.session.add(user_deck)

        associated_commander_id = None # Initialize
        non_null_associations = {} # Initialize

        if deck_type_id == COMMANDER_DECK_TYPE_ID and commander:
            associations = {
                "partner_id": partner_id_str,
                "friends_forever_id": friends_forever_id_str,
                "time_lord_doctor_id": time_lord_doctor_id_str,
                "doctor_companion_id": doctor_companion_id_str,
                "background_id": background_id_str
            }

            for key, value_str in associations.items():
                if value_str is not None:
                    try:
                        non_null_associations[key] = int(value_str)
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

            else: # Case where no associated commander was provided
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
        # Populate commander IDs in response only if a CommanderDeck was created
        if deck_type_id == COMMANDER_DECK_TYPE_ID and 'commander_deck' in locals() and commander_deck:
             response_data["deck"]["commander_id"] = commander_deck.commander_id
             if commander_deck.associated_commander_id:
                 # Determine which key was used for the association to put it back in response
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
@login_required
def user_decks():
    user_id = session.get('user_id')
    deck_type_filter = request.args.get('deck_type_id', default=None)
    tags_param = request.args.get('tags', default=None)

    tag_ids = None
    if tags_param:
        try:
            tag_ids = [int(tag_id.strip()) for tag_id in tags_param.split(',') if tag_id.strip().isdigit()]
            if not tag_ids:
                 tag_ids = None
        except ValueError:
             return jsonify({"error": "Invalid character in 'tags' parameter. Use comma-separated integers."}), 400

    try:
        # Assume get_user_decks uses modern syntax internally
        user_decks_result = get_user_decks(user_id, deck_type_id=deck_type_filter, tag_ids=tag_ids)

        if not user_decks_result:
            return jsonify([]), 200

        # Assume get_all_decks_stats uses modern syntax internally
        all_stats = get_all_decks_stats(user_id)
        stats_map = {deck_stat["id"]: deck_stat for deck_stat in all_stats}

        decks_list = []
        for deck, deck_type in user_decks_result:
            deck_stats = stats_map.get(deck.id, {})
            # Format last_match timestamp if it exists
            last_match_iso = None
            if deck_stats.get("last_match"):
                 # Make sure it's aware UTC before formatting
                 ts = deck_stats["last_match"]
                 if ts.tzinfo is None:
                      aware_ts = ts.replace(tzinfo=timezone.utc)
                 else:
                      aware_ts = ts.astimezone(timezone.utc)
                 last_match_iso = aware_ts.isoformat()

            decks_list.append({
                "id": deck.id,
                "creation_date": deck.creation_date.isoformat() if deck.creation_date else None, # Format creation date
                "name": deck.name,
                "type": deck.deck_type_id,
                "deck_type": {
                    "id": deck_type.id if deck_type else None,
                    "name": deck_type.name if deck_type else None
                },
                "win_rate": deck_stats.get("win_rate", 0),
                "total_matches": deck_stats.get("total_matches", 0),
                "total_wins": deck_stats.get("total_wins", 0),
                "last_match": last_match_iso, # Use formatted timestamp
                "tags": [{"id": tag.id, "name": tag.name} for tag in deck.tags]
            })

        return jsonify(decks_list), 200

    except Exception as e:
         logger.error(f"Error fetching user decks for user {user_id}: {e}", exc_info=True)
         return jsonify({"error": "Failed to fetch user decks"}), 500

@decks_bp.route("/decks/<int:deck_id>", methods=["PATCH"])
@login_required
def update_deck(deck_id):
    user_id = session.get('user_id')

    deck = db.session.get(Deck, deck_id)
    if not deck or deck.user_id != user_id:
        return jsonify({"error": f"Deck with id {deck_id} not found for this user."}), 404

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
        logger.error(f"Database error during deck update for deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e)}), 500

@decks_bp.route("/decks/<int:deck_id>", methods=["DELETE"])
@login_required
def delete_deck(deck_id):
    user_id = session.get('user_id')

    deck = db.session.get(Deck, deck_id)
    if not deck or deck.user_id != user_id:
        return jsonify({"error": f"Deck with id {deck_id} not found for this user."}), 404

    try:
        db.session.delete(deck)
        db.session.commit()
        logger.info(f"Deck {deck_id} deleted successfully by user {user_id}")
        return jsonify({"message": f"Deck {deck_id} deleted successfully"}), 200

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error during deck deletion {deck_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Cannot delete deck due to existing related data (e.g., matches). Ensure DB cascades are set.", "details": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during deck deletion {deck_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred during deletion.", "details": str(e)}), 500

@decks_bp.route('/decks/<int:deck_id>/tags', methods=['POST'])
@login_required
def add_tag_to_deck(deck_id):
    current_user_id = session.get('user_id')
    data = request.get_json()

    if not data or 'tag_id' not in data:
        return jsonify({"error": "Missing 'tag_id' in request body"}), 400

    tag_id = data.get('tag_id')
    if not isinstance(tag_id, int):
         return jsonify({"error": "'tag_id' must be an integer"}), 400

    deck = db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
    if not deck or deck.user_id != current_user_id:
        return jsonify({"error": "Deck not found or not owned by user"}), 404

    tag_to_add = db.session.get(Tag, tag_id)
    if not tag_to_add or tag_to_add.user_id != current_user_id:
        return jsonify({"error": "Tag not found or not owned by user"}), 404

    if tag_to_add in deck.tags:
         return jsonify({"message": "Tag already associated with this deck"}), 200

    try:
        deck.tags.append(tag_to_add)
        db.session.commit()
        return jsonify({"message": "Tag associated successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding tag {tag_id} to deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while associating the tag"}), 500

@decks_bp.route('/decks/<int:deck_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def remove_tag_from_deck(deck_id, tag_id):
    current_user_id = session.get('user_id')

    deck = db.session.get(Deck, deck_id, options=[selectinload(Deck.tags)])
    if not deck or deck.user_id != current_user_id:
        return jsonify({"error": "Deck not found or not owned by user"}), 404

    tag_to_remove = db.session.get(Tag, tag_id)
    if not tag_to_remove or tag_to_remove.user_id != current_user_id:
        return jsonify({"error": "Tag not found or not owned by user"}), 404

    if tag_to_remove not in deck.tags:
         return jsonify({"error": "Tag is not associated with this deck"}), 404

    try:
        deck.tags.remove(tag_to_remove)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing tag {tag_id} from deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500