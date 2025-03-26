from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.services.decks.get_user_decks_service import get_user_decks
from backend.services.matches.match_service import get_all_decks_stats

user_decks_bp = Blueprint("user_decks", __name__, url_prefix="/api")

@user_decks_bp.route("/user_decks", methods=["GET"])
@jwt_required()
def user_decks():
    user_id = get_jwt_identity()
    user_decks = get_user_decks(user_id)

    if not user_decks:
        return jsonify([]), 200
    
    stats = {deck["id"]: deck for deck in get_all_decks_stats(user_id)}

    decks_list = [
        {
                "id": deck.id,
                "name": deck.name,
                "type": deck.deck_type_id,
            "deck_type": {
                "name": deck_type.name
            },
            "win_rate": stats.get(deck.id, {}).get("win_rate", 0),
            "total_matches": stats.get(deck.id, {}).get("total_matches", 0),
            "total_wins": stats.get(deck.id, {}).get("total_wins", 0)
        } 
        for deck, deck_type in user_decks
    ]

    print(f"stats = {stats}")
    print(f"decks_list = {decks_list}")

    return jsonify(decks_list), 200