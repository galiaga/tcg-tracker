# backend/routes/matches.py

from flask import jsonify, Blueprint, request, session
from backend.utils.decorators import login_required
from backend import db
from backend.models import Match, UserDeck, Tag, Deck, DeckType
from backend.models.tag import match_tags
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select
import logging
from datetime import timezone, datetime

matches_bp = Blueprint("matches", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# --- Constants ---
RESULT_WIN_ID = 0
RESULT_LOSS_ID = 1
RESULT_DRAW_ID = 2
VALID_RESULTS = {RESULT_WIN_ID, RESULT_LOSS_ID, RESULT_DRAW_ID}
RESULT_MAP_TEXT = {
    RESULT_WIN_ID: "Victory",
    RESULT_LOSS_ID: "Defeat",
    RESULT_DRAW_ID: "Draw"
}

# --- Helper Functions ---
def format_timestamp(dt):
    if not dt: return None
    aware_dt = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return aware_dt.isoformat()

# --- API Endpoints ---

@matches_bp.route("/log_match", methods=["POST"])
@login_required
def log_match():
    user_id = session.get('user_id')
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid request body. JSON expected."}), 400

    deck_id_str = data.get("deck_id")
    match_result_str = data.get("match_result")

    if deck_id_str is None or match_result_str is None:
        return jsonify({"error": "Missing required fields: deck_id, match_result"}), 400

    try:
        deck_id = int(deck_id_str)
        match_result = int(match_result_str)
    except (ValueError, TypeError):
         return jsonify({"error": "Invalid type for deck_id or match_result. Integers required."}), 400

    if match_result not in VALID_RESULTS:
         return jsonify({"error": f"Invalid match_result value. Must be one of {VALID_RESULTS}"}), 400

    stmt_ud = select(UserDeck).where(UserDeck.user_id == user_id, UserDeck.deck_id == deck_id)
    user_deck_entry = db.session.scalars(stmt_ud).first()

    if not user_deck_entry:
        logger.warning(f"User {user_id} attempted to log match for non-owned/non-existent deck {deck_id}")
        return jsonify({"error": "Deck not found or not owned by user."}), 404

    try:
        new_match = Match(result=match_result, user_deck_id=user_deck_entry.id) # is_active defaults True
        db.session.add(new_match)
        db.session.commit()
        db.session.refresh(new_match)
        logger.info(f"Match logged successfully (ID: {new_match.id}) for user {user_id}, deck {deck_id}")
        return jsonify({
            "message": "Match logged successfully",
            "match": {
                "id": new_match.id, "timestamp": format_timestamp(new_match.timestamp),
                "result": new_match.result, "result_text": RESULT_MAP_TEXT.get(new_match.result, "Unknown"),
                "user_deck_id": new_match.user_deck_id, "deck_id": deck_id, "is_active": new_match.is_active
            }
            }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error logging match for user {user_id}, deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e)}), 500


@matches_bp.route('/matches/<int:match_id>/tags', methods=['POST'])
@login_required
def add_tag_to_match(match_id):
    current_user_id = session.get('user_id')
    data = request.get_json()
    if not data or 'tag_id' not in data: return jsonify({"error": "Missing 'tag_id' in request body"}), 400
    try: tag_id = int(data['tag_id'])
    except (ValueError, TypeError): return jsonify({"error": "'tag_id' must be an integer"}), 400

    # Find active match owned by user
    stmt_match = select(Match).join(Match.user_deck).where(
        Match.id == match_id, UserDeck.user_id == current_user_id, Match.is_active == True
    ).options(selectinload(Match.tags))
    match = db.session.scalars(stmt_match).first()
    if not match: return jsonify({"error": "Match not found or not available for tagging"}), 404

    # Find tag owned by user (add is_active check if Tag model has it)
    stmt_tag = select(Tag).where(Tag.id==tag_id, Tag.user_id==current_user_id)
    tag_to_add = db.session.scalars(stmt_tag).first()
    if not tag_to_add: return jsonify({"error": "Tag not found or not available"}), 404

    if tag_to_add in match.tags: return jsonify({"message": "Tag already associated with this match"}), 200

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
@login_required
def remove_tag_from_match(match_id, tag_id):
    current_user_id = session.get('user_id')

    # Find active match owned by user
    stmt_match = select(Match).join(Match.user_deck).where(
        Match.id == match_id, UserDeck.user_id == current_user_id, Match.is_active == True
    ).options(selectinload(Match.tags))
    match = db.session.scalars(stmt_match).first()
    if not match: return jsonify({"error": "Match not found or not available for tag removal"}), 404

    # Find the tag
    tag_to_remove = db.session.get(Tag, tag_id)
    if not tag_to_remove: return jsonify({"error": "Tag not found"}), 404
    if tag_to_remove not in match.tags: return jsonify({"error": "Tag is not associated with this match"}), 404

    try:
        match.tags.remove(tag_to_remove)
        db.session.commit()
        logger.info(f"Tag {tag_id} removed from match {match_id} by user {current_user_id}")
        return '', 204 # Success, no content
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing tag {tag_id} from match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500

@matches_bp.route('/matches/<int:match_id>', methods=['DELETE'])
@login_required
def delete_match(match_id):
    """Soft deletes a specific match record."""
    current_user_id = session.get('user_id')

    # Find active match owned by user
    stmt = select(Match).join(Match.user_deck).where(
        Match.id == match_id, UserDeck.user_id == current_user_id, Match.is_active == True
    )
    match_to_soft_delete = db.session.scalars(stmt).first()

    if not match_to_soft_delete:
        logger.warning(f"User {current_user_id} failed attempt to delete non-existent, unauthorized, or inactive match {match_id}.")
        return jsonify({"error": "Match not found or cannot be deleted"}), 404

    try:
        # Perform soft delete using model method
        match_to_soft_delete.soft_delete()
        db.session.commit()
        logger.info(f"Match {match_id} soft deleted successfully by user {current_user_id}.")
        return '', 204 # Success, no content
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error soft deleting match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while deleting the match."}), 500