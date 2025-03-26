from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from backend import db

from backend.models.deck import Deck

decks_bp = Blueprint("decks_api", __name__, url_prefix="/api")

@decks_bp.route("/decks", methods=["GET"])
@jwt_required()
def get_user_decks():
    decks = Deck.query.all()
    decks_list = [{"id": deck.id, "deck_name": deck.name} for deck in decks]
    return jsonify(decks_list)
