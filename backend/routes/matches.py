# backend/routes/matches.py

from flask import jsonify, Blueprint, request, session, current_app
from backend.utils.decorators import login_required
from backend import db, limiter
from backend.models import LoggedMatch, Tag, Deck # DeckType might not be needed if format is gone
from backend.models.logged_match import match_tags
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete
import logging
from datetime import timezone, datetime

matches_bp = Blueprint("matches", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# --- Constants ---
# Assuming LoggedMatchResult enum is defined in models.logged_match
# If not, define or import it here. For simplicity, using direct values.
RESULT_WIN = 0
RESULT_LOSS = 1
RESULT_DRAW = 2
VALID_RESULTS = {RESULT_WIN, RESULT_LOSS, RESULT_DRAW}
RESULT_MAP_TEXT = {
    RESULT_WIN: "Win", # Changed from Victory/Defeat for consistency with frontend
    RESULT_LOSS: "Loss",
    RESULT_DRAW: "Draw"
}

# --- Helper Functions ---
def format_timestamp(dt):
    if not dt: return None
    # Ensure datetime is timezone-aware (UTC) before formatting
    aware_dt = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return aware_dt.isoformat()

# --- API Endpoints ---

@matches_bp.route("/log_match", methods=["POST"])
@limiter.limit("60 per minute") # Consider if this limit is appropriate for frequent logging
@login_required
def log_match():
    user_id = session.get('user_id')
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid request body. JSON expected."}), 400

    deck_id_str = data.get("deck_id")
    match_result_str = data.get("result")
    player_position_str = data.get("player_position") # New field
    tag_names = data.get('tags', []) # Assuming tags are passed as a list of names
    opponent_description = data.get('opponent_description', None)
    # match_format is removed

    if deck_id_str is None or match_result_str is None:
        # player_position is optional for now to support older data or non-tracked games
        return jsonify({"error": "Missing required fields: deck_id, result"}), 400

    try:
        deck_id = int(deck_id_str)
        match_result = int(match_result_str)
        player_position = int(player_position_str) if player_position_str is not None else None
    except (ValueError, TypeError):
         return jsonify({"error": "Invalid type for deck_id, result, or player_position. Integers required."}), 400

    if match_result not in VALID_RESULTS:
         return jsonify({"error": f"Invalid result value. Must be one of {VALID_RESULTS}"}), 400

    if player_position is not None and not (1 <= player_position <= 4):
        return jsonify({"error": "Invalid player position. Must be between 1 and 4."}), 400

    # Ensure the deck exists, belongs to the user, and is active
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id, is_active=True).first()
    if not deck:
        logger.warning(f"User {user_id} attempted to log match for non-owned, inactive, or non-existent deck {deck_id}")
        return jsonify({"error": "Active deck not found or not owned by user."}), 404

    try:
        new_match = LoggedMatch(
            result=match_result,
            logger_user_id=user_id,
            deck_id=deck_id,
            timestamp=datetime.now(timezone.utc),
            opponent_description=opponent_description,
            player_position=player_position # Added new field
            # match_format is removed
        )
        db.session.add(new_match)
        db.session.flush() # Flush to get new_match.id for tag association

        # Handle tags
        if tag_names and isinstance(tag_names, list):
            tags_to_associate = []
            for name_or_id in tag_names: # Assuming frontend might send names or IDs
                tag = None
                if isinstance(name_or_id, int): # If ID is sent
                    tag = Tag.query.filter_by(id=name_or_id, user_id=user_id).first()
                elif isinstance(name_or_id, str) and name_or_id.strip(): # If name is sent
                    tag_name = name_or_id.strip()
                    tag = Tag.query.filter_by(user_id=user_id, name=tag_name).first()
                    if not tag: # Create tag if it doesn't exist for the user
                        tag = Tag(user_id=user_id, name=tag_name)
                        db.session.add(tag)
                        # No need to flush here, will be flushed before commit or handled by relationship
                if tag:
                    tags_to_associate.append(tag)
            
            if tags_to_associate:
                new_match.tags.extend(tags_to_associate)

        db.session.commit()
        logger.info(f"Match logged successfully (ID: {new_match.id}) for user {user_id}, deck {deck_id}")

        # Return comprehensive match details
        return jsonify({
            "message": "Match logged successfully",
            "match": {
                "id": new_match.id,
                "timestamp": format_timestamp(new_match.timestamp),
                "result": new_match.result,
                "result_text": RESULT_MAP_TEXT.get(new_match.result, "Unknown"),
                "deck_id": new_match.deck_id,
                "logger_user_id": new_match.logger_user_id,
                "opponent_description": new_match.opponent_description,
                "player_position": new_match.player_position, # Added
                # "match_format": new_match.match_format, # Removed
                "is_active": new_match.is_active,
                "tags": [{"id": t.id, "name": t.name} for t in new_match.tags]
            }
            }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error logging match for user {user_id}, deck {deck_id}: {e}", exc_info=True)
        # Provide more detail in debug mode, generic message otherwise
        error_detail = str(e) if current_app.debug else "An internal error occurred"
        return jsonify({"error": "Database error", "details": error_detail}), 500


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
    ).options(selectinload(LoggedMatch.tags)) # Eager load tags
    match = db.session.scalars(stmt_match).first()

    if not match:
        return jsonify({"error": "Match not found or not available for tagging"}), 404

    tag_to_add = Tag.query.filter_by(id=tag_id, user_id=current_user_id).first()
    if not tag_to_add:
        return jsonify({"error": "Tag not found or not owned by user"}), 404

    if tag_to_add in match.tags:
        return jsonify({"message": "Tag already associated with this match"}), 200 # Or 200 if idempotent

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
    ) # No need to eager load tags if using direct delete from association
    match = db.session.scalars(stmt_match).first()

    if not match:
        return jsonify({"error": "Match not found or not available for tag removal"}), 404

    # Check if the association exists directly (more robust than 'tag in match.tags' before removal)
    association_exists_stmt = select(match_tags).where(
        match_tags.c.match_id == match_id,
        match_tags.c.tag_id == tag_id
    )
    association_exists = db.session.execute(association_exists_stmt).first()

    if not association_exists:
         return jsonify({"error": "Tag is not associated with this match"}), 404

    try:
        # Delete directly from the association table
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
        LoggedMatch.is_active == True # Only allow deleting active matches
    )
    match_to_soft_delete = db.session.scalars(stmt).first()

    if not match_to_soft_delete:
        logger.warning(f"User {current_user_id} failed attempt to delete non-existent, unauthorized, or inactive match {match_id}.")
        return jsonify({"error": "Match not found or cannot be deleted"}), 404

    try:
        match_to_soft_delete.soft_delete() # Call the method from the model
        db.session.commit()
        logger.info(f"Match {match_id} soft deleted successfully by user {current_user_id}.")
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error soft deleting match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while deleting the match."}), 500