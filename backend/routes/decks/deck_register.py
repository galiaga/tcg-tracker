from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.models.user import User
from backend.models.deck import Deck
from backend.models.user_deck import UserDeck
from backend.models.commander_deck import CommanderDeck

deck_register_bp = Blueprint("deck_register", __name__, url_prefix="/api")

COMMANDER_DECK_TYPE_ID = 7

@deck_register_bp.route("/register_deck", methods=["POST"])
@jwt_required()
def register_deck():
    # Aquí el código original de register_deck
    if request.method == "GET":
        return jsonify({"error": "This endpoint only supports POST requests"}), 405

    user_id = get_jwt_identity()
    print(f"🔹 user_id obtenido desde JWT: {user_id}")
    data = request.get_json()
    deck_name = data.get("deck_name")
    deck_type_id = data.get("deck_type")

    # Convert deck_type_id to int
    try:
        deck_type_id = int(deck_type_id)
    except ValueError:
        pass

    commander_id = data.get("commander_id")

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    if not deck_name:
        return jsonify({"error": "Missing required fields"}), 400
    if (deck_type_id == COMMANDER_DECK_TYPE_ID) and not commander_id:
        return jsonify({"error": "Commander ID is required for Commander decks"}), 400
    
    try:
        new_deck = Deck(user_id=user_id, name=deck_name, deck_type_id=deck_type_id)
        db.session.add(new_deck)
        db.session.commit()

        user_deck = UserDeck(user_id=user_id, deck_id=new_deck.id)
        db.session.add(user_deck)
        
        if commander_id:
            commander_deck = CommanderDeck(deck_id=new_deck.id, commander_id=commander_id)
            db.session.add(commander_deck)

        db.session.commit()

        return jsonify({
            "message": "Deck registered successfully",
            "deck": {
                "id": new_deck.id,
                "name": new_deck.name,
                "deck_type": deck_type_id,
                "commander_id": commander_id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Database error: {e}") 
        return jsonify({"error": "Database error", "details": str(e)}), 500