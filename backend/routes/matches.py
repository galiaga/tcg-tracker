# backend/routes/matches.py

from flask import jsonify, Blueprint, request, session, current_app
from backend.utils.decorators import login_required
from backend import db, limiter
from backend.models import LoggedMatch, Tag, Deck, Commander # Ensure Commander is imported
# Import the new model for opponent commanders in a match
from backend.models.opponent_commander_in_match import OpponentCommanderInMatch 
from backend.models.logged_match import match_tags # For direct association table operations if needed
from sqlalchemy.orm import selectinload, joinedload # joinedload for eager loading opponent commanders
from sqlalchemy import select, delete
import logging
from datetime import timezone, datetime

matches_bp = Blueprint("matches", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# --- Constants ---
RESULT_WIN = 0
RESULT_LOSS = 1
RESULT_DRAW = 2
VALID_RESULTS = {RESULT_WIN, RESULT_LOSS, RESULT_DRAW}
RESULT_MAP_TEXT = {
    RESULT_WIN: "Win",
    RESULT_LOSS: "Loss",
    RESULT_DRAW: "Draw"
}
VALID_COMMANDER_ROLES = {"primary", "partner", "background", "friends_forever", "doctor_companion", "time_lord_doctor"}


# --- Helper Functions ---
def format_timestamp(dt):
    if not dt: return None
    aware_dt = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return aware_dt.isoformat()

# --- API Endpoints ---

@matches_bp.route("/log_match", methods=["POST"])
@limiter.limit("60 per minute")
@login_required
def log_match():
    user_id = session.get('user_id')
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid request body. JSON expected."}), 400

    # --- Extract required fields ---
    deck_id_str = data.get("deck_id")
    match_result_str = data.get("result")
    player_position_str = data.get("player_position") # Player's turn order/seat

    # --- Extract optional fields ---
    player_mulligans_str = data.get("player_mulligans")
    pod_notes = data.get("pod_notes")
    tag_names_or_ids = data.get('tags', [])
    
    # Expected payload for opponent commanders:
    # "opponent_commanders_by_seat": {
    #     "1": [ {"id": 123, "role": "primary"}, {"id": 124, "role": "partner"} ], // Seat 1 opponents
    #     "3": [ {"id": 456, "role": "primary"} ], // Seat 3 opponent (if player is e.g. seat 2)
    #     // etc. for other opponent seats
    # }
    opponent_commanders_payload = data.get("opponent_commanders_by_seat", {})


    # --- Validate required fields ---
    if deck_id_str is None or match_result_str is None or player_position_str is None:
        return jsonify({"error": "Missing required fields: deck_id, result, or player_position"}), 400

    try:
        deck_id = int(deck_id_str)
        match_result = int(match_result_str)
        player_position = int(player_position_str) 
        
        player_mulligans = None
        if player_mulligans_str is not None:
            player_mulligans = int(player_mulligans_str)
            if player_mulligans < 0:
                return jsonify({"error": "Player mulligans cannot be negative."}), 400
        
        # Validate opponent_commanders_payload structure
        parsed_opponent_commanders = [] # Will store tuples of (seat, commander_id, role)
        if not isinstance(opponent_commanders_payload, dict):
            return jsonify({"error": "opponent_commanders_by_seat must be an object."}), 400

        for seat_str, commanders_in_seat_list in opponent_commanders_payload.items():
            try:
                seat = int(seat_str)
                if not (1 <= seat <= 4) or seat == player_position:
                    # Silently ignore invalid seats or player's own seat if sent by frontend
                    continue 
                
                if not isinstance(commanders_in_seat_list, list):
                     return jsonify({"error": f"Commanders for seat {seat} must be a list."}), 400

                for cmd_data in commanders_in_seat_list:
                    if not isinstance(cmd_data, dict) or "id" not in cmd_data or "role" not in cmd_data:
                        return jsonify({"error": f"Invalid commander data format for seat {seat}. Expected {{'id': ..., 'role': ...}}."}), 400
                    
                    cmd_id = int(cmd_data["id"])
                    role = cmd_data["role"].lower()

                    if role not in VALID_COMMANDER_ROLES:
                        return jsonify({"error": f"Invalid role '{role}' for commander at seat {seat}."}), 400
                    if not db.session.get(Commander, cmd_id):
                        return jsonify({"error": f"Commander ID {cmd_id} for opponent at seat {seat} (role: {role}) not found."}), 400
                    
                    parsed_opponent_commanders.append({'seat_number': seat, 'commander_id': cmd_id, 'role': role})

            except (ValueError, TypeError):
                return jsonify({"error": "Invalid format within opponent_commanders_by_seat. Seat keys must be numbers, commander IDs must be integers."}), 400
                
    except (ValueError, TypeError):
         return jsonify({"error": "Invalid type for numeric fields (deck_id, result, player_position, or mulligans)."}), 400

    if match_result not in VALID_RESULTS:
         return jsonify({"error": f"Invalid result value."}), 400
    if not (1 <= player_position <= 4):
        return jsonify({"error": "Invalid player position."}), 400

    deck = Deck.query.filter_by(id=deck_id, user_id=user_id, is_active=True).first()
    if not deck:
        return jsonify({"error": "Active deck not found or not owned by user."}), 404

    try:
        new_match = LoggedMatch(
            result=match_result,
            logger_user_id=user_id,
            deck_id=deck_id,
            timestamp=datetime.now(timezone.utc),
            player_position=player_position,
            player_mulligans=player_mulligans,
            pod_notes=pod_notes
        )
        db.session.add(new_match)
        # We need to flush to get new_match.id before creating OpponentCommanderInMatch entries
        db.session.flush() 

        # Create OpponentCommanderInMatch entries
        for opp_cmd_data in parsed_opponent_commanders:
            ocim_entry = OpponentCommanderInMatch(
                logged_match_id=new_match.id,
                seat_number=opp_cmd_data['seat_number'],
                commander_id=opp_cmd_data['commander_id'],
                role=opp_cmd_data['role']
            )
            db.session.add(ocim_entry)

        # Handle tags
        if tag_names_or_ids and isinstance(tag_names_or_ids, list):
            tags_to_associate = []
            for name_or_id in tag_names_or_ids:
                tag = None
                if isinstance(name_or_id, int):
                    tag = Tag.query.filter_by(id=name_or_id, user_id=user_id).first()
                elif isinstance(name_or_id, str) and name_or_id.strip():
                    tag_name = name_or_id.strip()
                    tag = Tag.query.filter_by(user_id=user_id, name=tag_name).first()
                    if not tag:
                        tag = Tag(user_id=user_id, name=tag_name)
                        db.session.add(tag)
                if tag:
                    tags_to_associate.append(tag)
            if tags_to_associate:
                new_match.tags.extend(tags_to_associate)

        db.session.commit()
        logger.info(f"Match logged successfully (ID: {new_match.id}) for user {user_id}, deck {deck_id}")

        # Prepare response data - Eager load opponent commanders for the response
        # This is to ensure the response includes the newly created opponent commander details.
        final_match_data = LoggedMatch.query.options(
            joinedload(LoggedMatch.opponent_commanders).joinedload(OpponentCommanderInMatch.commander),
            selectinload(LoggedMatch.tags) # Keep existing eager load for tags
        ).get(new_match.id)


        response_match_data = {
            "id": final_match_data.id,
            "timestamp": format_timestamp(final_match_data.timestamp),
            "result": final_match_data.result,
            "result_text": RESULT_MAP_TEXT.get(final_match_data.result, "Unknown"),
            "deck_id": final_match_data.deck_id,
            "logger_user_id": final_match_data.logger_user_id,
            "player_position": final_match_data.player_position,
            "player_mulligans": final_match_data.player_mulligans,
            "pod_notes": final_match_data.pod_notes,
            "is_active": final_match_data.is_active,
            "tags": [{"id": t.id, "name": t.name} for t in final_match_data.tags],
            "opponent_commanders_by_seat": {} # Populate this based on final_match_data.opponent_commanders
        }
        
        for oc in final_match_data.opponent_commanders:
            seat_key = str(oc.seat_number)
            if seat_key not in response_match_data["opponent_commanders_by_seat"]:
                response_match_data["opponent_commanders_by_seat"][seat_key] = []
            response_match_data["opponent_commanders_by_seat"][seat_key].append({
                "id": oc.commander_id,
                "name": oc.commander.name if oc.commander else "Unknown Commander", # Access via relationship
                "role": oc.role
            })
        
        return jsonify({
            "message": "Match logged successfully",
            "match": response_match_data
            }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error logging match for user {user_id}, deck {deck_id}: {e}", exc_info=True)
        error_detail = str(e) if current_app.debug else "An internal error occurred"
        return jsonify({"error": "Database error", "details": error_detail}), 500


# --- Other Match Routes (add_tag_to_match, remove_tag_from_match, delete_match) ---
# These routes generally do not need to change for this specific feature of logging opponent commanders,
# as they operate on the LoggedMatch itself or its direct tag associations.
# The soft_delete method on LoggedMatch will handle cascade deletion of OpponentCommanderInMatch
# entries due to `ondelete='CASCADE'` on the ForeignKey and `cascade="all, delete-orphan"` on the relationship.

@matches_bp.route('/matches/<int:match_id>/tags', methods=['POST'])
@limiter.limit("60 per minute")
@login_required
def add_tag_to_match(match_id):
    current_user_id = session.get('user_id')
    data = request.get_json()
    if not data or 'tag_id' not in data: return jsonify({"error": "Missing 'tag_id' in request body"}), 400
    try: tag_id = int(data['tag_id'])
    except (ValueError, TypeError): return jsonify({"error": "'tag_id' must be an integer"}), 400

    stmt_match = select(LoggedMatch).where(
        LoggedMatch.id == match_id,
        LoggedMatch.logger_user_id == current_user_id,
        LoggedMatch.is_active == True
    ).options(selectinload(LoggedMatch.tags))
    match = db.session.scalars(stmt_match).first()

    if not match:
        return jsonify({"error": "Match not found or not available for tagging"}), 404

    tag_to_add = Tag.query.filter_by(id=tag_id, user_id=current_user_id).first()
    if not tag_to_add:
        return jsonify({"error": "Tag not found or not owned by user"}), 404

    if tag_to_add in match.tags:
        return jsonify({"message": "Tag already associated with this match"}), 200

    try:
        match.tags.append(tag_to_add)
        db.session.commit()
        logger.info(f"Tag {tag_id} added to match {match_id} by user {current_user_id}")
        return jsonify({"message": "Tag associated successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding tag to match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while associating the tag"}), 500

@matches_bp.route('/matches/<int:match_id>/tags/<int:tag_id>', methods=['DELETE'])
@limiter.limit("60 per minute")
@login_required
def remove_tag_from_match(match_id, tag_id):
    current_user_id = session.get('user_id')

    stmt_match = select(LoggedMatch).where(
        LoggedMatch.id == match_id,
        LoggedMatch.logger_user_id == current_user_id,
        LoggedMatch.is_active == True
    )
    match = db.session.scalars(stmt_match).first()

    if not match:
        return jsonify({"error": "Match not found or not available for tag removal"}), 404

    association_exists_stmt = select(match_tags).where(
        match_tags.c.match_id == match_id,
        match_tags.c.tag_id == tag_id
    )
    association_exists = db.session.execute(association_exists_stmt).first()

    if not association_exists:
         return jsonify({"error": "Tag is not associated with this match"}), 404

    try:
        delete_stmt = delete(match_tags).where(
            match_tags.c.match_id == match_id,
            match_tags.c.tag_id == tag_id
        )
        db.session.execute(delete_stmt)
        db.session.commit()
        logger.info(f"Tag {tag_id} removed from match {match_id} by user {current_user_id}")
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing tag {tag_id} from match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500


@matches_bp.route('/matches/<int:match_id>', methods=['DELETE'])
@limiter.limit("60 per minute")
@login_required
def delete_match(match_id):
    current_user_id = session.get('user_id')

    stmt = select(LoggedMatch).where(
        LoggedMatch.id == match_id,
        LoggedMatch.logger_user_id == current_user_id,
        LoggedMatch.is_active == True
    )
    match_to_soft_delete = db.session.scalars(stmt).first()

    if not match_to_soft_delete:
        logger.warning(f"User {current_user_id} failed attempt to delete non-existent, unauthorized, or inactive match {match_id}.")
        return jsonify({"error": "Match not found or cannot be deleted"}), 404

    try:
        match_to_soft_delete.soft_delete() # This will also handle cascade for OpponentCommanderInMatch due to model setup
        db.session.commit()
        logger.info(f"Match {match_id} soft deleted successfully by user {current_user_id}.")
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error soft deleting match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while deleting the match."}), 500