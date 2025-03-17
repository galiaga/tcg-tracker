from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import get_db

decks_bp = Blueprint("decks", __name__, url_prefix="/api")

@decks_bp.route("/register_deck", methods=["POST"])
@jwt_required()
def register_deck():
    db = get_db()

    # Captura datos JSON
    user_id = get_jwt_identity()
    data = request.get_json()
    deck_name = data.get("deck_name")
    deck_type = data.get("deck_type")
    commander_id = data.get("commander_id")

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    if not deck_name:
        return jsonify({"error": "Missing required fields"}), 400

    user = db.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    username = user["username"] if user else "Unknown" 

    try:
        cursor = db.execute("INSERT INTO decks (deck_name, deck_type_id) VALUES (?, ?)", (deck_name, deck_type,))
        deck_id = cursor.lastrowid

        db.execute("INSERT INTO user_decks (user_id, deck_id) VALUES (?, ?)", (user_id, deck_id))

        if commander_id: 
            db.execute("INSERT INTO commander_decks (deck_id, commander_id) VALUES (?, ?)",(deck_id, commander_id))
        db.commit()

        return jsonify({
            "message": "Deck registered successfully",
            "deck": {
                "id": deck_id,
                "name": deck_name,
                "deck_type": deck_type,
                "commander_id": commander_id
            },
            "username": username
        }), 201

    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}") 
        return jsonify({"error": "Database error", "details": str(e)}), 500

@decks_bp.route("/decks", methods=["GET"])
@jwt_required()
def get_user_decks():
    db = get_db()
    user_id = get_jwt_identity()

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    
    decks = db.execute("SELECT user_decks.id, decks.deck_name FROM user_decks JOIN decks ON user_decks.deck_id = decks.id WHERE user_decks.user_id = ?;",(user_id,)).fetchall()

    decks_list = [{"id": deck["id"], "deck_name": deck["deck_name"]} for deck in decks]

    return jsonify(decks_list)
