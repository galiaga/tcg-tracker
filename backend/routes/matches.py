# backend/routes/matches.py

from flask import jsonify, Blueprint, request, session, current_app
from backend.utils.decorators import login_required
from backend import db, limiter
from backend.models import LoggedMatch, Tag, Deck, DeckType
from backend.models.logged_match import match_tags 
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete
import logging
from datetime import timezone, datetime

matches_bp = Blueprint("matches", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# --- Constants ---
RESULT_WIN_ID = 1
RESULT_LOSS_ID = 0
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
@limiter.limit("60 per minute")
@login_required
def log_match():
    user_id = session.get('user_id')
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid request body. JSON expected."}), 400

    deck_id_str = data.get("deck_id")
    match_result_str = data.get("result")
    tag_names = data.get('tags', [])
    opponent_description = data.get('opponent_description', None)
    match_format = data.get('match_format', None)

    if deck_id_str is None or match_result_str is None:
        return jsonify({"error": "Missing required fields: deck_id, result"}), 400

    try:
        deck_id = int(deck_id_str)
        match_result = int(match_result_str)
    except (ValueError, TypeError):
         return jsonify({"error": "Invalid type for deck_id or result. Integers required."}), 400

    if match_result not in VALID_RESULTS:
         return jsonify({"error": f"Invalid result value. Must be one of {VALID_RESULTS}"}), 400

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
            match_format=match_format
        )
        db.session.add(new_match)
        db.session.flush()

        if tag_names and isinstance(tag_names, list):
            tags_to_associate = []
            for name in tag_names:
                if isinstance(name, str) and name.strip():
                    tag = Tag.query.filter_by(user_id=user_id, name=name.strip()).first()
                    if not tag:
                        tag = Tag(user_id=user_id, name=name.strip())
                        db.session.add(tag)
                        db.session.flush()
                    # Check if already added (optional, depends on relationship config)
                    # This check might be less reliable than querying association table
                    # For adding, append is usually fine, duplicates might be handled by DB/relationship
                    tags_to_associate.append(tag) # Simplification: just try adding
            if tags_to_associate:
                new_match.tags.extend(tags_to_associate)

        db.session.commit()
        logger.info(f"Match logged successfully (ID: {new_match.id}) for user {user_id}, deck {deck_id}")

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
                "match_format": new_match.match_format,
                "is_active": new_match.is_active,
                "tags": [{"id": t.id, "name": t.name} for t in new_match.tags]
            }
            }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error logging match for user {user_id}, deck {deck_id}: {e}", exc_info=True)
        error_detail = str(e) if current_app.debug else "An internal error occurred"
        return jsonify({"error": "Database error", "details": error_detail}), 500


@matches_bp.route('/matches/<int:match_id>/tags', methods=['POST'])
@limiter.limit("60 per minute")
@login_required # Ensure decorator is here
def add_tag_to_match(match_id):
    # --- DEBUG PRINT ---
    print(f"--- DEBUG: Entered add_tag_to_match route for match_id: {match_id} ---", flush=True)
    # --- END DEBUG PRINT ---
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
        print(f"--- DEBUG add_tag_to_match: Match {match_id} not found/owned by user {current_user_id}, returning 404 ---", flush=True)
        return jsonify({"error": "Match not found or not available for tagging"}), 404

    tag_to_add = Tag.query.filter_by(id=tag_id, user_id=current_user_id).first()
    if not tag_to_add:
        print(f"--- DEBUG add_tag_to_match: Tag {tag_id} not found/owned by user {current_user_id}, returning 404 ---", flush=True)
        return jsonify({"error": "Tag not found or not owned by user"}), 404

    # Check if already associated before appending
    if tag_to_add in match.tags:
        print(f"--- DEBUG add_tag_to_match: Tag {tag_id} already associated, returning 200 ---", flush=True)
        return jsonify({"message": "Tag already associated with this match"}), 200

    try:
        match.tags.append(tag_to_add)
        db.session.commit()
        logger.info(f"Tag {tag_id} added to match {match_id} by user {current_user_id}")
        # Ensure 201 is returned on success
        print(f"--- DEBUG add_tag_to_match: Commit successful, returning 201 ---", flush=True)
        return jsonify({"message": "Tag associated successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding tag to match {match_id} for user {current_user_id}: {e}", exc_info=True)
        print(f"--- DEBUG add_tag_to_match: Exception during commit, returning 500 ---", flush=True)
        return jsonify({"error": "An unexpected error occurred while associating the tag"}), 500

@matches_bp.route('/matches/<int:match_id>/tags/<int:tag_id>', methods=['DELETE'])
@limiter.limit("60 per minute")
@login_required # Ensure decorator is here
def remove_tag_from_match(match_id, tag_id):
    current_user_id = session.get('user_id')
    # --- DEBUG PRINT ---
    print(f"--- DEBUG: Entered remove_tag_from_match route: user={current_user_id}, match={match_id}, tag={tag_id} ---", flush=True)
    # --- END DEBUG PRINT ---

    # Find active match logged by the current user
    stmt_match = select(LoggedMatch).where(
        LoggedMatch.id == match_id,
        LoggedMatch.logger_user_id == current_user_id,
        LoggedMatch.is_active == True
    )
    match = db.session.scalars(stmt_match).first()

    if not match:
        print(f"--- DEBUG remove_tag_from_match: Match {match_id} not found or not owned by user {current_user_id}, returning 404 ---", flush=True)
        return jsonify({"error": "Match not found or not available for tag removal"}), 404

    # --- Explicitly check if the association exists in the join table ---
    association_exists_stmt = select(match_tags).where(
        match_tags.c.match_id == match_id,
        match_tags.c.tag_id == tag_id
    )
    association_exists = db.session.execute(association_exists_stmt).first()
    print(f"--- DEBUG remove_tag_from_match: Association exists check result: {association_exists} ---", flush=True)
    # --- End Check ---

    if not association_exists:
         print(f"--- DEBUG remove_tag_from_match: Association not found, returning 404 ---", flush=True)
         return jsonify({"error": "Tag is not associated with this match"}), 404

    try:
        # --- Delete directly from association table ---
        delete_stmt = delete(match_tags).where(
            match_tags.c.match_id == match_id,
            match_tags.c.tag_id == tag_id
        )
        print(f"--- DEBUG remove_tag_from_match: Executing delete statement ---", flush=True)
        result = db.session.execute(delete_stmt)
        print(f"--- DEBUG remove_tag_from_match: Delete result rowcount: {result.rowcount} ---", flush=True)
        # --- End Delete ---

        db.session.commit()
        print(f"--- DEBUG remove_tag_from_match: Commit successful, returning 204 ---", flush=True)
        return '', 204 # Success, no content
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing tag {tag_id} from match {match_id} for user {current_user_id}: {e}", exc_info=True)
        print(f"--- DEBUG remove_tag_from_match: Exception during delete/commit, returning 500 ---", flush=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500


@matches_bp.route('/matches/<int:match_id>', methods=['DELETE'])
@limiter.limit("60 per minute")
@login_required # Ensure decorator is here
def delete_match(match_id):
    """Soft deletes a specific match record logged by the user."""
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
        match_to_soft_delete.soft_delete()
        db.session.commit()
        logger.info(f"Match {match_id} soft deleted successfully by user {current_user_id}.")
        return '', 204 # Success, no content
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error soft deleting match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while deleting the match."}), 500