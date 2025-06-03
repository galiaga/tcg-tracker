# backend/routes/decks.py

from flask import Blueprint, jsonify, request, Response, session, current_app
from sqlalchemy import select, true # Added true for boolean comparisons
from sqlalchemy.orm import selectinload
import json # Not explicitly used, can be removed if not needed elsewhere
import logging
from datetime import timezone, datetime

from backend import db, limiter
from backend.models import CommanderDeck, Commander, UserDeck, Deck, Tag, DeckType
from backend.services.matches.match_service import get_deck_stats, get_all_decks_stats
from backend.services.decks.get_user_decks_service import get_user_decks # Assuming this is updated for Commander only
from backend.services.decks.get_commander_attributes_service import get_commander_attributes_by_id
from backend.utils.decorators import login_required

decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

COMMANDER_DECK_TYPE_ID = 7
COMMANDER_DECK_TYPE_NAME = "Commander" # Consistent naming

# --- Read Operations ---

@decks_bp.route("/decks", methods=["GET"])
@limiter.limit("60 per minute")
@login_required
def get_all_decks():
    # This route might need re-evaluation. Does it return ALL decks in the system?
    # Or all decks for the current user? The name implies all, but login_required implies user-specific.
    # For now, assuming it's intended for user's decks, similar to /user_decks but maybe less detail.
    user_id = session.get('user_id')
    stmt = select(Deck).where(Deck.user_id == user_id, Deck.is_active == true())
    decks = db.session.scalars(stmt).all()
    # It's good practice to return more info than just id/name if this is a general "get my decks" endpoint
    decks_list = [{"id": deck.id, "name": deck.name} for deck in decks] # Changed deck_name to name
    return jsonify(decks_list)

@decks_bp.route("/decks/<int:deck_id>", methods=["GET"])
@limiter.limit("60 per minute")
@login_required
def deck_details(deck_id):
    user_id = session.get('user_id')
    deck = Deck.query.options(
        selectinload(Deck.tags),
        selectinload(Deck.deck_type) # Eager load deck_type
    ).filter_by(
        id=deck_id, user_id=user_id, is_active=True
    ).first()

    if not deck:
        return jsonify({"error": f"Active deck with id {deck_id} not found for this user."}), 404

    deck_data = deck.to_dict() # Assuming to_dict() provides basic fields
    # Ensure format_name is included from deck_type
    deck_data["format_name"] = deck.deck_type.name if deck.deck_type else COMMANDER_DECK_TYPE_NAME

    stats = get_deck_stats(user_id, deck_id)
    deck_data.update({
        "win_rate": stats.get("win_rate", 0) if stats else 0,
        "total_matches": stats.get("total_matches", 0) if stats else 0,
        "total_wins": stats.get("total_wins", 0) if stats else 0
    })

    # Initialize all potential associated commander fields to None for consistent response
    deck_data["commander_id"] = None
    deck_data["commander_name"] = None
    deck_data["partner_id"] = None
    deck_data["partner_name"] = None # If you want to return names too
    deck_data["friends_forever_id"] = None
    deck_data["friends_forever_name"] = None
    deck_data["doctor_companion_id"] = None
    deck_data["doctor_companion_name"] = None
    deck_data["time_lord_doctor_id"] = None
    deck_data["time_lord_doctor_name"] = None
    deck_data["background_id"] = None
    deck_data["background_name"] = None
    # This key is generic, the specific ones above are more informative if possible
    deck_data["associated_commander_id"] = None
    deck_data["associated_commander_name"] = None


    if deck.deck_type_id == COMMANDER_DECK_TYPE_ID:
        stmt_cd = select(CommanderDeck).where(CommanderDeck.deck_id == deck.id)
        commander_deck_info = db.session.scalars(stmt_cd).first()
        if commander_deck_info:
            if commander_deck_info.commander_id:
                main_commander_obj = db.session.get(Commander, commander_deck_info.commander_id)
                if main_commander_obj:
                    deck_data["commander_id"] = main_commander_obj.id
                    deck_data["commander_name"] = main_commander_obj.name
            
            if commander_deck_info.associated_commander_id:
                assoc_commander_obj = db.session.get(Commander, commander_deck_info.associated_commander_id)
                if assoc_commander_obj:
                    deck_data["associated_commander_id"] = assoc_commander_obj.id # Generic key
                    deck_data["associated_commander_name"] = assoc_commander_obj.name # Generic key

                    # Determine the specific type of association for more detailed response keys
                    if main_commander_obj: # Need main commander to determine pairing type
                        if main_commander_obj.partner and assoc_commander_obj.partner:
                            deck_data["partner_id"] = assoc_commander_obj.id
                            deck_data["partner_name"] = assoc_commander_obj.name
                        elif main_commander_obj.friends_forever and assoc_commander_obj.friends_forever:
                            deck_data["friends_forever_id"] = assoc_commander_obj.id
                            deck_data["friends_forever_name"] = assoc_commander_obj.name
                        elif main_commander_obj.time_lord_doctor and assoc_commander_obj.doctor_companion:
                            deck_data["doctor_companion_id"] = assoc_commander_obj.id # The companion's ID
                            deck_data["doctor_companion_name"] = assoc_commander_obj.name
                        elif main_commander_obj.doctor_companion and assoc_commander_obj.time_lord_doctor:
                            deck_data["time_lord_doctor_id"] = assoc_commander_obj.id # The Doctor's ID
                            deck_data["time_lord_doctor_name"] = assoc_commander_obj.name
                        elif main_commander_obj.choose_a_background and assoc_commander_obj.background:
                            deck_data["background_id"] = assoc_commander_obj.id
                            deck_data["background_name"] = assoc_commander_obj.name


    deck_data["tags"] = [{"id": tag.id, "name": tag.name} for tag in deck.tags]
    return jsonify(deck_data), 200


@decks_bp.route("/user_decks", methods=["GET"])
@limiter.limit("60 per minute")
@login_required
def user_decks():
    user_id = session.get('user_id')
    tags_param = request.args.get('tags', default=None)
    tag_ids = None

    if tags_param:
        try:
            tag_ids = [int(tag_id.strip()) for tag_id in tags_param.split(',') if tag_id.strip().isdigit()]
            if not tag_ids: tag_ids = None # Ensure it's None if list becomes empty
        except ValueError:
             # Invalid characters in tags should ideally be ignored or handled gracefully
             # For now, let's assume they result in no tag filtering if parsing fails
             logger.warning(f"Invalid characters in 'tags' parameter for user {user_id}: {tags_param}")
             tag_ids = None # Or return 400 if strict:
             # return jsonify({"error": "Invalid character in 'tags' parameter. Use comma-separated integers."}), 400


    # deck_type_id filter is removed from frontend, so backend should assume Commander
    # The get_user_decks service should be aware of this or default to Commander.
    # Passing COMMANDER_DECK_TYPE_ID explicitly to be clear.
    try:
        user_decks_result = get_user_decks(user_id, deck_type_id=str(COMMANDER_DECK_TYPE_ID), tag_ids=tag_ids)
        if not user_decks_result: return jsonify([]), 200

        all_stats = get_all_decks_stats(user_id)
        stats_map = {deck_stat["id"]: deck_stat for deck_stat in all_stats}
        decks_list = []

        for deck, deck_type_obj in user_decks_result: # deck_type_obj will always be Commander
            deck_stats = stats_map.get(deck.id, {})
            last_match_iso = None
            if deck_stats.get("last_match"):
                 ts = deck_stats["last_match"]
                 aware_ts = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
                 last_match_iso = aware_ts.isoformat()

            decks_list.append({
                "id": deck.id,
                "creation_date": deck.creation_date.isoformat() if deck.creation_date else None,
                "name": deck.name,
                "deck_type_id": deck.deck_type_id,
                "format_name": deck_type_obj.name if deck_type_obj else COMMANDER_DECK_TYPE_NAME, # Added format_name
                "win_rate": deck_stats.get("win_rate", 0),
                "total_matches": deck_stats.get("total_matches", 0),
                "total_wins": deck_stats.get("total_wins", 0),
                "last_match": last_match_iso, # Renamed from last_match_date to last_match for consistency
                "tags": [{"id": tag.id, "name": tag.name} for tag in deck.tags]
            })
        return jsonify(decks_list), 200
    except Exception as e:
         logger.error(f"Error fetching user decks for user {user_id}: {e}", exc_info=True)
         return jsonify({"error": "Failed to fetch user decks"}), 500

# --- Create Operation ---

@decks_bp.route("/register_deck", methods=["POST"])
@limiter.limit("30 per minute") # Stricter limit for creation
@login_required
def register_deck():
    user_id = session.get('user_id')
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid request body"}), 400

    deck_name = data.get("deck_name")
    # Deck type is now implicitly Commander
    deck_type_id = COMMANDER_DECK_TYPE_ID

    if not deck_name or not deck_name.strip(): # Check for empty or whitespace-only
        return jsonify({"error": "Deck Name is required."}), 400

    commander_id_str = data.get("commander_id")
    if not commander_id_str:
        return jsonify({"error": "A Commander is required."}), 400 # Match test error
    
    try:
        commander_id = int(commander_id_str)
        commander = db.session.get(Commander, commander_id)
        if not commander: return jsonify({"error": "Selected Commander not found."}), 404
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid Commander ID format."}), 400

    # Extract all potential associated commander IDs
    partner_id_str = data.get("partner_id")
    friends_forever_id_str = data.get("friends_forever_id")
    doctor_companion_id_str = data.get("doctor_companion_id") # This is the ID of the Companion
    time_lord_doctor_id_str = data.get("time_lord_doctor_id") # This is the ID of the Doctor
    background_id_str = data.get("background_id")

    associated_commander_id = None
    assoc_key_used = None # To store which key was used (e.g., "partner_id")

    # Consolidate provided associated commander IDs
    provided_associations = []
    if partner_id_str: provided_associations.append(("partner_id", partner_id_str, "Partner", commander.partner, True)) # Main needs partner, assoc needs partner
    if friends_forever_id_str: provided_associations.append(("friends_forever_id", friends_forever_id_str, "Friends Forever", commander.friends_forever, True)) # Main needs FF, assoc needs FF
    if doctor_companion_id_str: provided_associations.append(("doctor_companion_id", doctor_companion_id_str, "Doctor's Companion", commander.time_lord_doctor, False)) # Main is Doctor, assoc is Companion
    if time_lord_doctor_id_str: provided_associations.append(("time_lord_doctor_id", time_lord_doctor_id_str, "Time Lord Doctor", commander.doctor_companion, False)) # Main is Companion, assoc is Doctor
    if background_id_str: provided_associations.append(("background_id", background_id_str, "Background", commander.choose_a_background, False)) # Main needs BG, assoc is BG

    if len(provided_associations) > 1:
        db.session.rollback()
        return jsonify({"error": "Only one associated commander type can be provided."}), 400
    
    # Validate main commander's requirement if no association provided
    if not provided_associations:
        if commander.partner: return jsonify({"error": f"'{commander.name}' requires a Partner commander."}), 400
        if commander.friends_forever: return jsonify({"error": f"'{commander.name}' requires a Friends Forever commander."}), 400
        if commander.time_lord_doctor: return jsonify({"error": f"'{commander.name}' requires a Doctor's Companion commander."}), 400
        if commander.doctor_companion: return jsonify({"error": f"'{commander.name}' requires a Time Lord Doctor commander."}), 400
        if commander.choose_a_background: return jsonify({"error": f"'{commander.name}' requires a Background commander."}), 400
        # If no associations provided and none required, proceed
    
    elif provided_associations:
        assoc_key_used, assoc_id_str, assoc_type_name, main_commander_ability_flag, _ = provided_associations[0]

        if not main_commander_ability_flag: # Check if main commander has the corresponding ability
            db.session.rollback()
            return jsonify({"error": f"'{commander.name}' cannot be paired with the selected {assoc_type_name}."}), 400

        try:
            associated_commander_id = int(assoc_id_str)
        except (ValueError, TypeError):
            db.session.rollback()
            return jsonify({"error": f"Invalid ID format for {assoc_type_name}."}), 400

        if commander_id == associated_commander_id:
            db.session.rollback()
            return jsonify({"error": "Commander and associated Commander cannot be the same."}), 400
        
        associated_commander = db.session.get(Commander, associated_commander_id)
        if not associated_commander:
            db.session.rollback()
            return jsonify({"error": f"Selected {assoc_type_name} not found."}), 404

        # Validate the associated commander's specific role
        is_valid_associated_role = False
        if assoc_key_used == "partner_id" and associated_commander.partner: is_valid_associated_role = True
        elif assoc_key_used == "friends_forever_id" and associated_commander.friends_forever: is_valid_associated_role = True
        elif assoc_key_used == "doctor_companion_id" and associated_commander.doctor_companion: is_valid_associated_role = True
        elif assoc_key_used == "time_lord_doctor_id" and associated_commander.time_lord_doctor: is_valid_associated_role = True
        elif assoc_key_used == "background_id" and associated_commander.background: is_valid_associated_role = True
        
        if not is_valid_associated_role:
            db.session.rollback()
            return jsonify({"error": f"'{associated_commander.name}' is not a valid {assoc_type_name}."}), 400

    # If all validations pass
    try:
        new_deck = Deck(user_id=user_id, name=deck_name, deck_type_id=deck_type_id)
        db.session.add(new_deck)
        db.session.flush() # Get ID for new_deck

        commander_deck_entry = CommanderDeck(
            deck_id=new_deck.id,
            commander_id=commander_id,
            associated_commander_id=associated_commander_id # This will be None if no valid association was made
        )
        db.session.add(commander_deck_entry)
        
        # Handle tags if provided (assuming 'tags' is a list of tag IDs)
        tag_ids = data.get("tags", [])
        if isinstance(tag_ids, list):
            for tag_id in tag_ids:
                if isinstance(tag_id, int):
                    tag = db.session.get(Tag, tag_id)
                    # Ensure tag exists and belongs to the user
                    if tag and tag.user_id == user_id:
                        new_deck.tags.append(tag)
                    else:
                        logger.warning(f"Tag ID {tag_id} not found or not owned by user {user_id} during deck registration.")
        
        db.session.commit()

        # Prepare response data, ensuring all keys are present
        response_deck_data = {
            "id": new_deck.id,
            "name": new_deck.name,
            "deck_type_id": new_deck.deck_type_id,
            "commander_id": commander_id,
            "partner_id": None,
            "friends_forever_id": None,
            "doctor_companion_id": None,
            "time_lord_doctor_id": None,
            "background_id": None,
            # "associated_commander_id": associated_commander_id # This is generic, specific keys are better
            "tags": [{"id": t.id, "name": t.name} for t in new_deck.tags]
        }
        if assoc_key_used and associated_commander_id:
            response_deck_data[assoc_key_used] = associated_commander_id
        
        return jsonify({ "message": "Deck registered successfully", "deck": response_deck_data }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck registration for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "details": str(e) if current_app.debug else "Internal Server Error"}), 500


# --- Update Operation (deck_details call needs to be consistent with its own response structure) ---
@decks_bp.route("/decks/<int:deck_id>", methods=["PATCH"])
@limiter.limit("60 per minute")
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
    
    if not updated: return jsonify({"message": "No changes detected"}), 200

    try:
        db.session.commit()
        # Re-fetch and serialize the deck to ensure the response is complete and consistent
        # Call the deck_details function which now returns a more complete object
        updated_deck_details_tuple = deck_details(deck_id) # This returns (jsonify_object, status_code)
        updated_deck_data = updated_deck_details_tuple[0].get_json() if updated_deck_details_tuple[1] == 200 else None

        if updated_deck_data:
            return jsonify({"message": "Deck updated successfully", "deck": updated_deck_data}), 200
        else:
            logger.error(f"Failed to re-fetch deck details after update for deck {deck_id}")
            # Fallback: return basic info if detailed re-fetch fails
            return jsonify({"message": "Deck updated, but failed to fetch full updated details", 
                            "deck": {"id": deck.id, "name": deck.name}}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck update for deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e) if current_app.debug else "Internal Server Error"}), 500


# --- Delete Operation ---
@decks_bp.route("/decks/<int:deck_id>", methods=["DELETE"])
@limiter.limit("60 per minute")
@login_required
def delete_deck(deck_id):
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "Authentication required."}), 401

    deck = Deck.query.filter_by(id=deck_id, user_id=user_id, is_active=True).first()
    if not deck:
        logger.warning(f"Attempt to delete non-existent, already deleted, or unauthorized deck {deck_id} by user {user_id}")
        return jsonify({"error": f"Deck with id {deck_id} not found or not accessible."}), 404

    try:
        deck.is_active = False
        deck.deleted_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Deck {deck_id} soft deleted successfully by user {user_id}")
        return jsonify({"message": f"Deck {deck_id} deleted successfully"}), 200 # Changed to 200 from 204 to allow message
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during deck soft deletion {deck_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred during deletion."}), 500

# --- Tag Operations (Mostly unchanged, ensure consistency) ---
@decks_bp.route('/decks/<int:deck_id>/tags', methods=['POST'])
@limiter.limit("60 per minute")
@login_required
def add_tag_to_deck(deck_id):
    current_user_id = session.get('user_id')
    data = request.get_json()
    if not data or 'tag_id' not in data: return jsonify({"error": "Missing 'tag_id' in request body"}), 400
    
    try:
        tag_id = int(data.get('tag_id'))
    except (ValueError, TypeError):
        return jsonify({"error": "'tag_id' must be a valid integer"}), 400

    deck = Deck.query.options(selectinload(Deck.tags)).filter_by(id=deck_id, user_id=current_user_id, is_active=True).first()
    if not deck: return jsonify({"error": "Active deck not found or not owned by user"}), 404

    tag_to_add = db.session.get(Tag, tag_id)
    if not tag_to_add or tag_to_add.user_id != current_user_id: return jsonify({"error": "Tag not found or not owned by user"}), 404
    if tag_to_add in deck.tags: return jsonify({"message": "Tag already associated with this deck"}), 200 # 200 OK if already there

    try:
        deck.tags.append(tag_to_add)
        db.session.commit()
        return jsonify({"message": "Tag associated successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding tag {tag_id} to deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while associating the tag"}), 500

@decks_bp.route('/decks/<int:deck_id>/tags/<int:tag_id>', methods=['DELETE'])
@limiter.limit("60 per minute")
@login_required
def remove_tag_from_deck(deck_id, tag_id):
    current_user_id = session.get('user_id')
    deck = Deck.query.options(selectinload(Deck.tags)).filter_by(id=deck_id, user_id=current_user_id, is_active=True).first()
    if not deck: return jsonify({"error": "Active deck not found or not owned by user"}), 404

    tag_to_remove = db.session.get(Tag, tag_id)
    if not tag_to_remove or tag_to_remove.user_id != current_user_id: return jsonify({"error": "Tag not found or not owned by user"}), 404
    if tag_to_remove not in deck.tags: return jsonify({"error": "Tag is not associated with this deck"}), 404 # Or 200 if idempotent

    try:
        deck.tags.remove(tag_to_remove)
        db.session.commit()
        return jsonify({"message": "Tag disassociated successfully"}), 204 # Changed from 204 to allow message
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing tag {tag_id} from deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500