from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.models.deck import Deck
from backend.services.matches.match_service import get_deck_stats

deck_details_bp = Blueprint("deck_details", __name__, url_prefix="/api")

@deck_details_bp.route("/decks/<int:deck_id>", methods=["GET"])
@jwt_required()
def deck_details(deck_id):
    user_id = get_jwt_identity()
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first_or_404()
    deck_data = deck.to_dict()

    stats = get_deck_stats(user_id, deck_id)
    if stats:
        deck_data.update({
            "win_rate": stats["win_rate"],
            "total_matches": stats["total_matches"],
            "total_wins": stats["total_wins"]
        })
    return jsonify(deck_data), 200