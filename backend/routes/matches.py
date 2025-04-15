from flask import jsonify, Blueprint, request, session
from backend.utils.decorators import login_required
from backend import db
from backend.models import Match, UserDeck, Tag, Deck, DeckType
from backend.models.tag import match_tags
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, delete 
import logging
from datetime import timezone

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

def format_timestamp(dt):
    """Helper function to ensure aware UTC timestamp before isoformat."""
    if not dt:
        return None
    if dt.tzinfo is None:
        aware_dt = dt.replace(tzinfo=timezone.utc)
    else:
        aware_dt = dt.astimezone(timezone.utc)
    return aware_dt.isoformat()

@matches_bp.route("/log_match", methods=["POST"])
@login_required
def log_match():
    user_id = session.get('user_id')
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

    stmt_ud = select(UserDeck).where(
        UserDeck.user_id == user_id,
        UserDeck.deck_id == deck_id
    )
    user_deck_entry = db.session.scalars(stmt_ud).first()

    if not user_deck_entry:
        logger.warning(f"User {user_id} attempted to log match for non-owned/non-existent deck {deck_id}")
        return jsonify({"error": "Deck not found or not owned by user."}), 404

    try:
        new_match = Match(result=match_result, user_deck_id=user_deck_entry.id)
        db.session.add(new_match)
        db.session.commit()
        db.session.refresh(new_match)

        logger.info(f"Match logged successfully (ID: {new_match.id}) for user {user_id}, deck {deck_id}")

        return jsonify({
            "message": "Match logged successfully",
            "match": {
                "id": new_match.id,
                "timestamp": format_timestamp(new_match.timestamp), 
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

@matches_bp.route('/matches_history', methods=['GET'])
@login_required
def get_matches_history():
    current_user_id = session.get('user_id')
    tag_ids_str = request.args.get('tags')
    deck_id_str = request.args.get('deck_id')

    try:
        stmt = select(Match).join(UserDeck, Match.user_deck_id == UserDeck.id)\
                            .where(UserDeck.user_id == current_user_id)

        deck_id = None
        if deck_id_str and deck_id_str.isdigit():
            try:
                deck_id = int(deck_id_str)
                stmt = stmt.where(UserDeck.deck_id == deck_id)
            except ValueError:
                 pass

        apply_tag_filter = False
        tag_ids = []
        if tag_ids_str:
            try:
                tag_ids = [int(tid) for tid in tag_ids_str.split(',') if tid.strip().isdigit()]
                if tag_ids:
                    apply_tag_filter = True
            except ValueError:
                return jsonify({"error": "Invalid tags format. Use comma-separated integers."}), 400

        if apply_tag_filter:
            stmt = stmt.join(match_tags, Match.id == match_tags.c.match_id)\
                       .where(match_tags.c.tag_id.in_(tag_ids))\
                       .distinct()

        stmt = stmt.options(
            joinedload(Match.user_deck)
                .joinedload(UserDeck.deck)
                .joinedload(Deck.deck_type),
            selectinload(Match.tags) 
        )
        stmt = stmt.order_by(Match.timestamp.desc())

        matches = db.session.scalars(stmt).unique().all()

        matches_list = []
        for match in matches:
            deck_info = None
            deck_type_info = None
            if match.user_deck and match.user_deck.deck:
                deck_info = {
                    'id': match.user_deck.deck.id,
                    'name': match.user_deck.deck.name
                }
                if match.user_deck.deck.deck_type:
                    deck_type_info = {
                         'id': match.user_deck.deck.deck_type.id,
                         'name': match.user_deck.deck.deck_type.name
                    }

            matches_list.append({
                'id': match.id,
                'result': match.result,
                'date': format_timestamp(match.timestamp), 
                'user_deck_id': match.user_deck_id,
                'deck': deck_info,
                'deck_type': deck_type_info,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in match.tags]
            })

        return jsonify(matches_list)

    except Exception as e:
        logger.error(f"Error fetching match history for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while fetching match history."}), 500


@matches_bp.route('/matches/<int:match_id>/tags', methods=['POST'])
@login_required
def add_tag_to_match(match_id):
    current_user_id = session.get('user_id')
    data = request.get_json()
    if not data or 'tag_id' not in data:
        return jsonify({"error": "Missing 'tag_id' in request body"}), 400

    tag_id = data.get('tag_id')
    if not isinstance(tag_id, int):
         return jsonify({"error": "'tag_id' must be an integer"}), 400

    stmt_match = select(Match).join(Match.user_deck).where(
        Match.id == match_id,
        UserDeck.user_id == current_user_id
    ).options(selectinload(Match.tags))
    match = db.session.scalars(stmt_match).first()


    if not match:
        return jsonify({"error": "Match not found or not owned by user"}), 404

    stmt_tag = select(Tag).where(Tag.id==tag_id, Tag.user_id==current_user_id)
    tag_to_add = db.session.scalars(stmt_tag).first()

    if not tag_to_add:
        return jsonify({"error": "Tag not found or not owned by user"}), 404

    if tag_to_add in match.tags:
         return jsonify({"message": "Tag already associated with this match"}), 200

    try:
        match.tags.append(tag_to_add)
        db.session.commit()
        return jsonify({"message": "Tag associated successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding tag to match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while associating the tag"}), 500


@matches_bp.route('/matches/<int:match_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def remove_tag_from_match(match_id, tag_id):
    current_user_id = session.get('user_id')

    stmt_match = select(Match).join(Match.user_deck).where(
        Match.id == match_id,
        UserDeck.user_id == current_user_id
    ).options(selectinload(Match.tags))
    match = db.session.scalars(stmt_match).first()

    if not match:
        return jsonify({"error": "Match not found or not owned by user"}), 404

    tag_to_remove = db.session.get(Tag, tag_id)
    if not tag_to_remove:
        return jsonify({"error": "Tag not found"}), 404

    if tag_to_remove.user_id != current_user_id:
         return jsonify({"error": "Tag not owned by user"}), 403

    if tag_to_remove not in match.tags:
         return jsonify({"error": "Tag is not associated with this match"}), 404

    try:
        match.tags.remove(tag_to_remove)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing tag {tag_id} from match {match_id} for user {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500