from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.services.match_history_service import get_matches_by_user

matches_history_bp = Blueprint("matches_history", __name__, url_prefix="/api")

@matches_history_bp.route("/matches_history", methods=["GET"])
@jwt_required()
def matches_history():
    user_id = get_jwt_identity()
    user_matches = get_matches_by_user(user_id)

    if not user_matches:
         return jsonify([]), 200

    matches_list = [
        {
            "id": user_match.id, 
            "result": user_match.result,
            "date": user_match.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "deck": {
                "id": deck.id,
                "name": deck.name,
                "type": deck.deck_type_id
            },
            "deck_type": {
                "name": deck_type.name
            }
        } 
        for user_match, deck, deck_type in user_matches
    ]

    return jsonify(matches_list), 200