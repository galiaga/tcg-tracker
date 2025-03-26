from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.models.deck import Deck

deck_details_bp = Blueprint("deck_details", __name__, url_prefix="/api")

@deck_details_bp.route("/decks/<int:deck_id>", methods=["GET"])
@jwt_required()
def deck_details(deck_id):
    user_id = get_jwt_identity()
    deck = Deck.query.get_or_404(deck_id)
    return jsonify(deck.to_dict()), 200