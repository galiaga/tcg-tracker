from flask import jsonify, Blueprint, request, session
from backend.utils.decorators import login_required
import logging
from backend.services.matches.match_history_service import get_matches_by_user

matches_history_bp = Blueprint("matches_history", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

@matches_history_bp.route("/matches_history", methods=["GET"])
@login_required
def matches_history():
    user_id = session.get('user_id')
    deck_id = request.args.get('deck_id', type=int, default=None)
    tags_param = request.args.get('tags', default=None)
    limit = request.args.get('limit', type=int, default=None)
    offset = request.args.get('offset', type=int, default=None)

    if limit is not None and limit <= 0:
         limit = None
    if offset is not None and offset < 0:
         offset = 0

    if limit is None:
        offset = None

    tag_ids = None
    if tags_param:
        try:
            tag_ids = [int(tag_id.strip()) for tag_id in tags_param.split(',') if tag_id.strip().isdigit()]
            if not tag_ids:
                 tag_ids = None
        except ValueError:
             return jsonify({"error": "Invalid character in 'tags' parameter. Use comma-separated integers."}), 400
        except Exception:
             tag_ids = None

    try:
        user_matches = get_matches_by_user(
            user_id,
            deck_id,
            limit=limit,
            offset=offset,
            tag_ids=tag_ids
        )

        if not user_matches:
             return jsonify([]), 200

        matches_list = []
        for user_match, deck, deck_type in user_matches:
             matches_list.append({
                 "id": user_match.id,
                 "result": user_match.result,
                 "date": user_match.timestamp.isoformat() if user_match.timestamp else None,
                 "deck": {
                     "id": deck.id if deck else None,
                     "name": deck.name if deck else "Unknown Deck",
                     "type": deck.deck_type_id if deck else None
                 },
                 "deck_type": {
                     "name": deck_type.name if deck_type else "Unknown Type"
                 },
                 "tags": [{"id": tag.id, "name": tag.name} for tag in user_match.tags] 
             })

        return jsonify(matches_list), 200

    except Exception as e:
         logger.error(f"Error fetching match history for user {user_id}: {e}", exc_info=True)
         return jsonify({"error": "Failed to fetch match history"}), 500