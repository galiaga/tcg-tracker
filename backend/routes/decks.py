from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db

from backend.models.user import User
from backend.models.deck import Deck
from backend.models.user_deck import UserDeck
from backend.models.commander_deck import CommanderDeck
from backend.services.user_service import get_user_by_username

decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")
COMMANDER_DECK_TYPE_ID = 7

@decks_bp.route("/decks", methods=["GET"])
@jwt_required()
def get_user_decks():
    user_id = get_jwt_identity()

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    
    decks = Deck.query.all()

    decks_list = [{"id": deck.id, "deck_name": deck.name} for deck in decks]

    return jsonify(decks_list)
