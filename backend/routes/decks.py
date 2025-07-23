# backend/routes/decks.py

from flask import Blueprint, jsonify, request, session, current_app
from sqlalchemy import select, true, func, case, or_
from sqlalchemy.orm import selectinload
import logging
from datetime import timezone, datetime

from backend import db, limiter
from backend.models import LoggedMatch, OpponentCommanderInMatch, CommanderDeck, Commander, UserDeck, Deck, Tag, DeckType
from backend.services.matches.match_service import get_all_decks_stats
from backend.utils.decorators import login_required
from backend.services.decks.deck_service import get_mulligan_stats_for_deck, get_deck_matchup_stats

decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

COMMANDER_DECK_TYPE_ID = 7
COMMANDER_DECK_TYPE_NAME = "Commander"


# --- Read Operations ---

@decks_bp.route("/decks", methods=["GET"])
@limiter.limit("60 per minute")
@login_required
def get_all_decks_simple(): # Renamed to avoid confusion with user_decks
    user_id = session.get('user_id')
    # This endpoint is for populating simple dropdowns, e.g., in Log Match Modal
    stmt = select(Deck.id, Deck.name).where(Deck.user_id == user_id, Deck.is_active == true()).order_by(Deck.name)
    decks = db.session.execute(stmt).mappings().all()
    return jsonify([dict(row) for row in decks])


@decks_bp.route("/decks/<int:deck_id>", methods=["GET"])
@limiter.limit("60 per minute")
@login_required
def deck_details(deck_id):
    user_id = session.get('user_id')
    
    include_turn_stats_param = request.args.get('include_turn_stats', 'false').lower() == 'true'
    include_matchup_stats_param = request.args.get('include_matchup_stats', 'false').lower() == 'true'
    recent_matches_limit_str = request.args.get('include_recent_matches', None)
    mulligan_stats = get_mulligan_stats_for_deck(deck_id, user_id)
    
    recent_matches_limit = None
    if recent_matches_limit_str:
        try:
            recent_matches_limit = int(recent_matches_limit_str)
            if recent_matches_limit <= 0:
                recent_matches_limit = 5 # Default to 5 if invalid positive number not given
        except ValueError:
            recent_matches_limit = None

    deck = Deck.query.options(
        selectinload(Deck.tags),
        selectinload(Deck.deck_type), # Still load to get the name, though it's always Commander
        selectinload(Deck.commander_decks).selectinload(CommanderDeck.commander)
    ).filter_by(
        id=deck_id, user_id=user_id, is_active=True
    ).first()

    if not deck:
        return jsonify({"error": f"Active deck with id {deck_id} not found for this user."}), 404

    deck_data = {
        "id": deck.id,
        "name": deck.name,
        "deck_url": deck.deck_url,
        "format_name": COMMANDER_DECK_TYPE_NAME,
        "tags": [{"id": tag.id, "name": tag.name} for tag in deck.tags],
        "commander_id": None, "commander_name": None,
        "associated_commander_id": None, "associated_commander_name": None,
        "partner_name": None, "friends_forever_name": None, "background_name": None,
        "doctor_companion_name": None, "time_lord_doctor_name": None,
        "mulligan_stats": mulligan_stats 
    }

    if deck.commander_decks and deck.commander_decks.commander:
        main_commander_obj = deck.commander_decks.commander
        deck_data["commander_id"] = main_commander_obj.id
        deck_data["commander_name"] = main_commander_obj.name
        if deck.commander_decks.associated_commander_id:
            assoc_commander_obj = db.session.get(Commander, deck.commander_decks.associated_commander_id)
            if assoc_commander_obj:
                deck_data["associated_commander_id"] = assoc_commander_obj.id
                deck_data["associated_commander_name"] = assoc_commander_obj.name
                if main_commander_obj.partner and assoc_commander_obj.partner: deck_data["partner_name"] = assoc_commander_obj.name
                elif main_commander_obj.friends_forever and assoc_commander_obj.friends_forever: deck_data["friends_forever_name"] = assoc_commander_obj.name
                elif main_commander_obj.time_lord_doctor and assoc_commander_obj.doctor_companion: deck_data["doctor_companion_name"] = assoc_commander_obj.name
                elif main_commander_obj.doctor_companion and assoc_commander_obj.time_lord_doctor: deck_data["time_lord_doctor_name"] = assoc_commander_obj.name
                elif main_commander_obj.choose_a_background and assoc_commander_obj.background: deck_data["background_name"] = assoc_commander_obj.name
    
    overall_stats_q = db.session.query(
        func.count(LoggedMatch.id).label("total_matches"),
        func.sum(case((LoggedMatch.result == 0, 1), else_=0)).label("total_wins") 
    ).filter(LoggedMatch.deck_id == deck_id, LoggedMatch.logger_user_id == user_id, LoggedMatch.is_active == true()).first()

    deck_data["total_matches"] = overall_stats_q.total_matches if overall_stats_q and overall_stats_q.total_matches is not None else 0
    deck_data["total_wins"] = overall_stats_q.total_wins if overall_stats_q and overall_stats_q.total_wins is not None else 0
    deck_data["win_rate"] = (deck_data["total_wins"] / deck_data["total_matches"] * 100) if deck_data["total_matches"] > 0 else 0.0

    if include_matchup_stats_param:
        deck_average_wr = deck_data["win_rate"]
        deck_data["matchup_stats"] = get_deck_matchup_stats(deck_id, deck_average_wr)

    if include_turn_stats_param:
        deck_data["turn_order_stats"] = {}
        for i in range(1, 5):
            stats = db.session.query(
                func.count(LoggedMatch.id).label("matches"),
                func.sum(case((LoggedMatch.result == 0, 1), else_=0)).label("wins")
            ).filter(
                LoggedMatch.deck_id == deck_id, LoggedMatch.logger_user_id == user_id,
                LoggedMatch.player_position == i, LoggedMatch.is_active == true()
            ).first()
            matches_count = stats.matches if stats and stats.matches is not None else 0
            wins_count = stats.wins if stats and stats.wins is not None else 0
            deck_data["turn_order_stats"][str(i)] = {
                "matches": matches_count,
                "wins": wins_count,
                "win_rate": (wins_count / matches_count * 100) if matches_count > 0 else 0.0
            }

    if recent_matches_limit and recent_matches_limit > 0:
        recent_matches_query = select(LoggedMatch.id, LoggedMatch.result, LoggedMatch.timestamp, LoggedMatch.player_position).where(
            LoggedMatch.deck_id == deck_id, LoggedMatch.logger_user_id == user_id,
            LoggedMatch.is_active == true()
        ).order_by(LoggedMatch.timestamp.desc()).limit(recent_matches_limit)
        matches_results = db.session.execute(recent_matches_query).mappings().all()
        deck_data["recent_matches"] = [dict(m) for m in matches_results]
    else:
        deck_data["recent_matches"] = []

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
            if not tag_ids: tag_ids = None
        except ValueError:
             return jsonify({"error": "Invalid character in 'tags' parameter. Use comma-separated integers."}), 400

    try:
        # Query directly, ensuring we only get Commander decks (deck_type_id = 7)
        stmt = select(Deck).options(selectinload(Deck.tags)).where(
            Deck.user_id == user_id,
            Deck.is_active == true(),
            Deck.deck_type_id == COMMANDER_DECK_TYPE_ID # Explicitly filter for Commander decks
        )
        if tag_ids:
            stmt = stmt.filter(Deck.tags.any(Tag.id.in_(tag_ids)))

        # Add default sorting if needed, e.g., by name or last played (requires more complex query for last played)
        # For now, let's rely on client-side sorting or a simpler default like name.
        # stmt = stmt.order_by(Deck.name) # Example sorting

        user_deck_objects = db.session.scalars(stmt).unique().all()

        if not user_deck_objects: return jsonify([]), 200

        all_stats_data = get_all_decks_stats(user_id) # This should be efficient
        stats_map = {deck_stat["id"]: deck_stat for deck_stat in all_stats_data}
        
        decks_list = []
        for deck in user_deck_objects:
            deck_stats = stats_map.get(deck.id, {})
            last_match_iso = None
            if deck_stats.get("last_match"): # last_match should be a datetime object or None
                 ts = deck_stats["last_match"]
                 if isinstance(ts, datetime):
                    aware_ts = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
                    last_match_iso = aware_ts.isoformat()
                 elif isinstance(ts, str): # If it's already a string, try to use it (less ideal)
                    last_match_iso = ts


            decks_list.append({
                "id": deck.id,
                "creation_date": deck.creation_date.isoformat() if deck.creation_date else None,
                "name": deck.name,
                "deck_type_id": deck.deck_type_id, # Should always be COMMANDER_DECK_TYPE_ID
                "format_name": COMMANDER_DECK_TYPE_NAME, # Always Commander
                "win_rate": deck_stats.get("win_rate", 0.0),
                "total_matches": deck_stats.get("total_matches", 0),
                "total_wins": deck_stats.get("total_wins", 0),
                "last_match": last_match_iso,
                "tags": [{"id": tag.id, "name": tag.name} for tag in deck.tags]
            })
        return jsonify(decks_list), 200
    except Exception as e:
         logger.error(f"Error fetching user decks for user {user_id}: {e}", exc_info=True)
         return jsonify({"error": "Failed to fetch user decks"}), 500

# --- Create Operation ---

@decks_bp.route("/register_deck", methods=["POST"])
@limiter.limit("30 per minute")
@login_required
def register_deck():
    user_id = session.get('user_id')
    data = request.get_json()
    
    logger.debug(f"Register deck request data: {data}") # Log raw data

    if not data: return jsonify({"error": "Invalid request body"}), 400

    deck_name = data.get("deck_name")
    deck_url = data.get("deck_url", None) 
    deck_type_id = COMMANDER_DECK_TYPE_ID
    logger.debug(f"Deck type ID automatically set to: {deck_type_id}")


    if not deck_name or not deck_name.strip():
        return jsonify({"error": "Deck Name is required."}), 400

    commander_id_str = data.get("commander_id")
    if not commander_id_str: # This check is correct
        return jsonify({"error": "A Commander is required."}), 400
    
    try:
        commander_id = int(commander_id_str)
        commander = db.session.get(Commander, commander_id)
        if not commander: return jsonify({"error": "Selected Commander not found."}), 404
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid Commander ID format."}), 400

    partner_id_str = data.get("partner_id")
    friends_forever_id_str = data.get("friends_forever_id")
    doctor_companion_id_str = data.get("doctor_companion_id")
    time_lord_doctor_id_str = data.get("time_lord_doctor_id")
    background_id_str = data.get("background_id")

    associated_commander_id = None
    assoc_key_used = None 
    
    provided_associations = []
    if partner_id_str: provided_associations.append(("partner_id", partner_id_str, "Partner", commander.partner, True))
    if friends_forever_id_str: provided_associations.append(("friends_forever_id", friends_forever_id_str, "Friends Forever", commander.friends_forever, True))
    if doctor_companion_id_str: provided_associations.append(("doctor_companion_id", doctor_companion_id_str, "Doctor's Companion", commander.time_lord_doctor, False))
    if time_lord_doctor_id_str: provided_associations.append(("time_lord_doctor_id", time_lord_doctor_id_str, "Time Lord Doctor", commander.doctor_companion, False))
    if background_id_str: provided_associations.append(("background_id", background_id_str, "Background", commander.choose_a_background, False))

    if len(provided_associations) > 1:
        return jsonify({"error": "Only one associated commander type can be provided."}), 400
    
    if not provided_associations:
        if commander.partner: return jsonify({"error": f"'{commander.name}' requires a Partner commander."}), 400
        if commander.friends_forever: return jsonify({"error": f"'{commander.name}' requires a Friends Forever commander."}), 400
        if commander.time_lord_doctor: return jsonify({"error": f"'{commander.name}' requires a Doctor's Companion commander."}), 400
        if commander.doctor_companion: return jsonify({"error": f"'{commander.name}' requires a Time Lord Doctor commander."}), 400
        if commander.choose_a_background: return jsonify({"error": f"'{commander.name}' requires a Background commander."}), 400
    
    elif provided_associations:
        assoc_key_used, assoc_id_str, assoc_type_name, main_commander_ability_flag, _ = provided_associations[0]

        if not main_commander_ability_flag:
            return jsonify({"error": f"'{commander.name}' cannot be paired with the selected {assoc_type_name}."}), 400
        try:
            associated_commander_id = int(assoc_id_str)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid ID format for {assoc_type_name}."}), 400
        if commander_id == associated_commander_id:
            return jsonify({"error": "Commander and associated Commander cannot be the same."}), 400
        associated_commander = db.session.get(Commander, associated_commander_id)
        if not associated_commander:
            return jsonify({"error": f"Selected {assoc_type_name} not found."}), 404

        is_valid_associated_role = False
        if assoc_key_used == "partner_id" and associated_commander.partner: is_valid_associated_role = True
        elif assoc_key_used == "friends_forever_id" and associated_commander.friends_forever: is_valid_associated_role = True
        elif assoc_key_used == "doctor_companion_id" and associated_commander.doctor_companion: is_valid_associated_role = True
        elif assoc_key_used == "time_lord_doctor_id" and associated_commander.time_lord_doctor: is_valid_associated_role = True
        elif assoc_key_used == "background_id" and associated_commander.background: is_valid_associated_role = True
        
        if not is_valid_associated_role:
            return jsonify({"error": f"'{associated_commander.name}' is not a valid {assoc_type_name}."}), 400

    try:
        new_deck = Deck(user_id=user_id, name=deck_name, deck_type_id=COMMANDER_DECK_TYPE_ID, deck_url=deck_url) 
        db.session.add(new_deck)
        db.session.flush()

        commander_deck_entry = CommanderDeck(
            deck_id=new_deck.id,
            commander_id=commander_id,
            associated_commander_id=associated_commander_id
        )
        db.session.add(commander_deck_entry)
        
        tag_ids = data.get("tags", [])
        if isinstance(tag_ids, list):
            for tag_id in tag_ids:
                if isinstance(tag_id, int):
                    tag = db.session.get(Tag, tag_id)
                    if tag and tag.user_id == user_id:
                        new_deck.tags.append(tag)
        
        db.session.commit()

        response_deck_data = {
            "id": new_deck.id,
            "name": new_deck.name,
            "deck_url": new_deck.deck_url,
            "deck_type_id": new_deck.deck_type_id,
            "commander_id": commander_id,
            "partner_id": None, "friends_forever_id": None, "doctor_companion_id": None,
            "time_lord_doctor_id": None, "background_id": None,
            "tags": [{"id": t.id, "name": t.name} for t in new_deck.tags]
        }
        if assoc_key_used and associated_commander_id:
            response_deck_data[assoc_key_used] = associated_commander_id
        
        return jsonify({ "message": "Deck registered successfully", "deck": response_deck_data }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck registration for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "details": str(e) if current_app.debug else "Internal Server Error"}), 500


# --- Update Operation ---
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

    if 'deck_url' in data:
        new_url = data['deck_url'].strip()
        if not new_url: return jsonify({"error": "Deck URL cannot be empty"}), 400
        if deck.deck_url != new_url: deck.deck_url = new_url; updated = True

    if not updated: return jsonify({"message": "No changes detected"}), 200

    try:
        db.session.commit()
        # Re-fetch details using the updated deck_details function to ensure consistency
        # This will return a tuple: (jsonify_object, status_code)
        response_tuple = deck_details(deck_id) 
        if response_tuple[1] == 200:
            updated_deck_data = response_tuple[0].get_json() # Extract JSON from jsonify object
            return jsonify({"message": "Deck updated successfully", "deck": updated_deck_data}), 200
        else: # Fallback if re-fetching details fails for some reason
            logger.error(f"Failed to re-fetch full deck details after update for deck {deck_id}")
            return jsonify({"message": "Deck updated, but failed to fetch full updated details", 
                            "deck": {"id": deck.id, "name": deck.name}}), 200 # Basic response
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during deck update for deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e) if current_app.debug else "Internal Server Error"}), 500


# --- Delete Operation ---
@decks_bp.route("/decks/<int:deck_id>", methods=["DELETE"])
@limiter.limit("60 per minute")
@login_required
def delete_deck(deck_id):
    # ... (This route seems mostly okay) ...
    user_id = session.get('user_id')
    if not user_id: return jsonify({"error": "Authentication required."}), 401

    deck = Deck.query.filter_by(id=deck_id, user_id=user_id, is_active=True).first()
    if not deck:
        logger.warning(f"Attempt to delete non-existent, already deleted, or unauthorized deck {deck_id} by user {user_id}")
        return jsonify({"error": f"Deck with id {deck_id} not found or not accessible."}), 404

    try:
        # deck.is_active = False # Model method should handle this
        # deck.deleted_at = datetime.now(timezone.utc)
        # db.session.add(deck)
        deck.soft_delete() # Use the model's method
        db.session.commit()
        logger.info(f"Deck {deck_id} soft deleted successfully by user {user_id}")
        return jsonify({"message": f"Deck {deck_id} deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during deck soft deletion {deck_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred during deletion."}), 500

# --- Tag Operations ---
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
    if tag_to_add in deck.tags: return jsonify({"message": "Tag already associated with this deck"}), 200

    try:
        deck.tags.append(tag_to_add)
        db.session.commit()
        return jsonify({"message": "Tag associated successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding tag {tag_id} to deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while associating the tag"}), 500

