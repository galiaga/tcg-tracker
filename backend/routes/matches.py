from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.models import Match, UserDeck, Deck
import logging

matches_bp = Blueprint("matches", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

RESULT_WIN_ID = 0
RESULT_LOSS_ID = 1
RESULT_DRAW_ID = 2
VALID_RESULTS = {RESULT_WIN_ID, RESULT_LOSS_ID, RESULT_DRAW_ID}
RESULT_MAP_TEXT = {
    RESULT_WIN_ID: "Victory",
    RESULT_LOSS_ID: "Defeat",
    RESULT_DRAW_ID: "Draw"
}

@matches_bp.route("/log_match", methods=["POST"])
@jwt_required()
def log_match():
    user_id = get_jwt_identity()

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body. JSON expected."}), 400

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

    user_deck_entry = db.session.query(UserDeck).filter_by(
        user_id=user_id,
        deck_id=deck_id
    ).first()

    if not user_deck_entry:
        logger.warning(f"User {user_id} attempted to log match for non-owned/non-existent deck {deck_id}")
        return jsonify({"error": "Deck not found or not owned by user."}), 404

    try:
        new_match = Match(result=match_result, user_deck_id=user_deck_entry.id)
        db.session.add(new_match)
        db.session.commit()

        logger.info(f"Match logged successfully (ID: {new_match.id}) for user {user_id}, deck {deck_id}")

        return jsonify({
            "message": "Match logged successfully",
            "match": {
                "id": new_match.id,
                "timestamp": new_match.timestamp.isoformat(),
                "result": new_match.result,
                "result_text": RESULT_MAP_TEXT.get(new_match.result, "Unknown"),
                "user_deck_id": new_match.user_deck_id,
                "deck_id": deck_id
            }
            }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error logging match for user {user_id}, deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "Database error", "details": str(e)}), 500