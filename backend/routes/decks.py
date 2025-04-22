# backend/routes/decks.py

from flask import Blueprint, jsonify, request, Response, session
from sqlalchemy import select, true
from sqlalchemy.orm import selectinload, joinedload
import json
import logging
from datetime import timezone, datetime

from backend import db
from backend.models import CommanderDeck, Commander, UserDeck, Deck, Tag, DeckType # Added DeckType
# Import the match service which calculates stats based on active matches
from backend.services.matches.match_service import get_deck_stats, get_all_decks_stats
# Import the deck fetching service
from backend.services.decks.get_user_decks_service import get_user_decks
from backend.services.decks.get_commander_attributes_service import get_commander_attributes_by_id
from backend.utils.decorators import login_required

decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# --- Constants ---
COMMANDER_DECK_TYPE_ID = 7 # Example ID for Commander format

# --- Read Operations ---

# ... (get_all_decks and deck_details remain the same as your provided version) ...
@decks_bp.route("/decks", methods=["GET"])
@login_required
def get_all_decks():
    # WARNING: This fetches ALL active decks, not just the user's. Adjust if needed.
    stmt = select(Deck).where(Deck.is_active == true())
    decks = db.session.scalars(stmt).all()
    decks_list = [{"id": deck.id, "deck_name": deck.name} for deck in decks]
    return jsonify(decks_list)

@decks_bp.route("/decks/<int:deck_id>", methods=["GET"])
@login_required
def deck_details(deck_id):
    user_id = session.get('user_id')
    deck = Deck.query.options(selectinload(Deck.tags), joinedload(Deck.deck_type)).filter_by( # Added deck_type join
        id=deck_id, user_id=user_id, is_active=True
    ).first()

    if not deck:
        return jsonify({"error": f"Active deck with id {deck_id} not found for this user."}), 404

    # Use base to_dict if appropriate, or build manually
    deck_data = {
        "id": deck.id,
        "name": deck.name,
        "deck_type": {"id": deck.deck_type.id, "name": deck.deck_type.name} if deck.deck_type else None,
        # Stats will be added next
    }

    stats = get_deck_stats(user_id, deck_id) # Service calculates based on active matches
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
                cmd_attrs = get_commander_attributes_by_id(commander_deck_info.commander_id)
                if cmd_attrs: deck_data["commander_name"] = cmd_attrs.get("name")
                deck_data["commander_id"] = commander_deck_info.commander_id
            if commander_deck_info.associated_commander_id:
                assoc_cmd_attrs = get_commander_attributes_by_id(commander_deck_info.associated_commander_id)
                if assoc_cmd_attrs: deck_data["associated_commander_name"] = assoc_cmd_attrs.get("name")
                deck_data["associated_commander_id"] = commander_deck_info.associated_commander_id

    # Filter tags if Tag model also has soft delete
    active_tags = [tag for tag in deck.tags if tag.is_active] if hasattr(Tag, 'is_active') else deck.tags
    deck_data["tags"] = [{"id": tag.id, "name": tag.name} for tag in active_tags]
    return jsonify(deck_data), 200


@decks_bp.route("/user_decks", methods=["GET"])
@login_required
def user_decks():
    """Fetches ACTIVE decks for the logged-in user with stats (active matches only)."""
    user_id = session.get('user_id')
    deck_type_filter = request.args.get('deck_type_id', default=None)
    tags_param = request.args.get('tags', default=None)
    tag_ids = None

    if tags_param:
        try:
            tag_ids = [int(tag_id.strip()) for tag_id in tags_param.split(',') if tag_id.strip().isdigit()]
            if not tag_ids: tag_ids = None
        except ValueError:
             return jsonify({"error": "Invalid character in 'tags' parameter. Use comma-separated integers."}), 400

    try:
        # 1. Fetch user decks - CRITICAL: Ensure get_user_decks service filters for Deck.is_active == True
        # If unsure, add the filter in the service OR filter the results here.
        user_decks_result = get_user_decks(user_id, deck_type_id=deck_type_filter, tag_ids=tag_ids)
        if not user_decks_result: return jsonify([]), 200

        # 2. Fetch stats (service already filters for active matches)
        all_stats = get_all_decks_stats(user_id)
        stats_map = {deck_stat["id"]: deck_stat for deck_stat in all_stats}
        decks_list = []

        # 3. Combine data, ensuring only active decks are included
        for deck, deck_type in user_decks_result:
            # *** Explicitly skip if the deck object itself is inactive ***
            # This is a safety check in case get_user_decks didn't filter
            if not deck.is_active:
                logger.debug(f"Skipping inactive deck {deck.id} in user_decks route.")
                continue

            # Get stats calculated by the service (based on active matches)
            deck_stats = stats_map.get(deck.id, {})

            # Format last match date
            last_match_iso = None
            if deck_stats.get("last_match"):
                 ts = deck_stats["last_match"]
                 # Ensure timezone awareness (assuming service returns naive UTC or timezone-aware)
                 aware_ts = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
                 last_match_iso = aware_ts.isoformat()

            # Filter tags if Tag model also has soft delete
            active_tags = [tag for tag in deck.tags if tag.is_active] if hasattr(Tag, 'is_active') else deck.tags

            # Append final data for the active deck
            decks_list.append({
                "id": deck.id,
                "creation_date": deck.creation_date.isoformat() if deck.creation_date else None,
                "name": deck.name,
                "type": deck.deck_type_id, # Keep original type ID if needed
                "deck_type": {"id": deck_type.id if deck_type else None, "name": deck_type.name if deck_type else None},
                # Use stats calculated by the service
                "win_rate": deck_stats.get("win_rate", 0),
                "total_matches": deck_stats.get("total_matches", 0),
                "total_wins": deck_stats.get("total_wins", 0),
                "last_match": last_match_iso,
                "tags": [{"id": tag.id, "name": tag.name} for tag in active_tags],
                "is_active": deck.is_active # Include status
            })

        return jsonify(decks_list), 200
    except Exception as e:
         logger.error(f"Error fetching user decks for user {user_id}: {e}", exc_info=True)
         return jsonify({"error": "Failed to fetch user decks"}), 500

# --- Create Operation ---
# ... (register_deck remains the same) ...
@decks_bp.route("/register_deck", methods=["POST"])
@login_required
def register_deck():
    user_id = session.get('user_id')
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid request body"}), 400

    deck_name = data.get("deck_name")
    deck_type_id_str = data.get("deck_type")
    if not deck_name: return jsonify({"error": "Add a Deck Name"}), 400
    if not deck_type_id_str: return jsonify({"error": "Deck type is required"}), 400

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
            if not commander: return jsonify({"error": "Selected Commander not found."}), 404
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

        associated_commander_id = None
        non_null_associations = {}
        commander_deck = None # Initialize commander_deck

        if deck_type_id == COMMANDER_DECK_TYPE_ID and commander:
            associations = {
                "partner_id": partner_id_str, "friends_forever_id": friends_forever_id_str,
                "time_lord_doctor_id": time_lord_doctor_id_str, "doctor_companion_id": doctor_companion_id_str,
                "background_id": background_id_str
            }
            for key, value_str in associations.items():
                if value_str is not None:
                    try: non_null_associations[key] = int(value_str)
                    except (ValueError, TypeError):
                        db.session.rollback(); return jsonify({"error": f"Invalid ID format for {key}."}), 400

            if len(non_null_associations) > 1:
                db.session.rollback(); return jsonify({"error": "Only one associated commander type can be included."}), 400

            associated_commander_id = next(iter(non_null_associations.values()), None)
            assoc_key = next(iter(non_null_associations.keys()), None)

            if associated_commander_id:
                if commander_id == associated_commander_id:
                    db.session.rollback(); return jsonify({"error": "Commander and associated Commander cannot be the same."}), 400
                associated_commander = db.session.get(Commander, associated_commander_id)
                if not associated_commander:
                    db.session.rollback(); return jsonify({"error": "Associated Commander not found."}), 404

                # Placeholder for validation logic
                # ASSOC_VALIDATION = { ... }
                # MAIN_REQ = { ... }
                # if not ASSOC_VALIDATION... or not MAIN_REQ... : rollback and return error

                commander_deck = CommanderDeck(deck_id=new_deck.id, commander_id=commander_id, associated_commander_id=associated_commander_id)
            else: # No associated commander provided
                 # Placeholder for validation logic (does commander require partner?)
                 # required_partner_type = next(...)
                 # if required_partner_type: rollback and return error
                commander_deck = CommanderDeck(deck_id=new_deck.id, commander_id=commander_id, associated_commander_id=None)

            if commander_deck: db.session.add(commander_deck)

        db.session.commit()

        response_data = { "message": "Deck registered successfully", "deck": { "id": new_deck.id, "name": new_deck.name, "deck_type": new_deck.deck_type_id, "commander_id": None, "partner_id": None, "friends_forever_id": None, "doctor_companion_id": None, "time_lord_doctor_id": None, "background_id": None } }
        if deck_type_id == COMMANDER_DECK_TYPE_ID and commander_deck:
             response_data["deck"]["commander_id"] = commander_deck.commander_id
             if commander_deck.associated_commander_id:
                 saved_assoc_key = next((k for k, v in non_null_associations.items() if v == commander_deck.associated_commander_id), None)
                 if saved_assoc_key: response_data["deck"][saved_assoc_key] = commander_deck.associated_commander_id

        return Response(json.dumps(response_data, indent=None), mimetype="application/json", status=201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck registration: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "details": str(e)}), 500

# --- Update Operation ---
# ... (update_deck remains the same) ...
@decks_bp.route("/decks/<int:deck_id>", methods=["PATCH"])
@login_required
def update_deck(deck_id):
    user_id = session.get('user_id')
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id, is_active=True).first()
    if not deck: return jsonify({"error": f"Active deck with id {deck_id} not found for this user."}), 404

    data = request.get_json()
    if not data: return jsonify({"error": "No update data provided"}), 400

    updated = False
    if 'deck_name' in data:
        new_name = data['deck_name'].strip()
        if not new_name: return jsonify({"error": "Deck Name cannot be empty"}), 400
        if deck.name != new_name: deck.name = new_name; updated = True

    # Add other updatable fields here if needed

    if not updated: return jsonify({"message": "No changes detected"}), 200

    try:
        db.session.commit()
        # Re-fetch stats to return the most up-to-date info
        updated_deck_data = deck.to_dict() # Use existing method if suitable
        stats = get_deck_stats(user_id, deck_id)
        updated_deck_data.update({ "win_rate": stats.get("win_rate", 0) if stats else 0, "total_matches": stats.get("total_matches", 0) if stats else 0, "total_wins": stats.get("total_wins", 0) if stats else 0 })
        # Manually add tags if to_dict doesn't include them
        active_tags = [tag for tag in deck.tags if tag.is_active] if hasattr(Tag, 'is_active') else deck.tags
        updated_deck_data["tags"] = [{"id": tag.id, "name": tag.name} for tag in active_tags]

        return jsonify({"message": "Deck updated successfully", "deck": updated_deck_data}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck update for deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e)}), 500


# --- Delete Operation (Soft Delete) ---
# ... (delete_deck remains the same - uses deck.soft_delete()) ...
@decks_bp.route("/decks/<int:deck_id>", methods=["DELETE"])
@login_required
def delete_deck(deck_id):
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "Authentication required."}), 401

    deck = Deck.query.filter_by(id=deck_id, user_id=user_id, is_active=True).first()
    if not deck:
        logger.warning(f"Attempt to delete non-existent, already deleted, or unauthorized deck {deck_id} by user {user_id}")
        return jsonify({"error": f"Deck with id {deck_id} not found or not accessible."}), 404

    try:
        deck.soft_delete() # Use the model method
        db.session.add(deck)
        db.session.commit()
        logger.info(f"Deck {deck_id} soft deleted successfully by user {user_id}")
        return jsonify({"message": f"Deck {deck_id} hidden successfully"}), 200 # Updated message
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during deck soft deletion {deck_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred during deletion."}), 500


# --- Tag Operations ---
# ... (add_tag_to_deck and remove_tag_from_deck remain the same - they already filter for active decks) ...
@decks_bp.route('/decks/<int:deck_id>/tags', methods=['POST'])
@login_required
def add_tag_to_deck(deck_id):
    current_user_id = session.get('user_id')
    data = request.get_json()
    if not data or 'tag_id' not in data: return jsonify({"error": "Missing 'tag_id' in request body"}), 400
    try: tag_id = int(data['tag_id'])
    except (ValueError, TypeError): return jsonify({"error": "'tag_id' must be an integer"}), 400

    deck = Deck.query.options(selectinload(Deck.tags)).filter_by(id=deck_id, user_id=current_user_id, is_active=True).first()
    if not deck: return jsonify({"error": "Active deck not found or not owned by user"}), 404

    tag_to_add = db.session.get(Tag, tag_id)
    # Add check for tag ownership and potentially tag.is_active
    if not tag_to_add or tag_to_add.user_id != current_user_id: return jsonify({"error": "Tag not found or not owned by user"}), 404
    if tag_to_add in deck.tags: return jsonify({"message": "Tag already associated with this deck"}), 200

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
    deck = Deck.query.options(selectinload(Deck.tags)).filter_by(id=deck_id, user_id=current_user_id, is_active=True).first()
    if not deck: return jsonify({"error": "Active deck not found or not owned by user"}), 404

    tag_to_remove = db.session.get(Tag, tag_id)
    # Add check for tag ownership
    if not tag_to_remove or tag_to_remove.user_id != current_user_id: return jsonify({"error": "Tag not found or not owned by user"}), 404
    if tag_to_remove not in deck.tags: return jsonify({"error": "Tag is not associated with this deck"}), 404

    try:
        deck.tags.remove(tag_to_remove)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing tag {tag_id} from deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500