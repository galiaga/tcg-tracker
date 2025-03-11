from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import get_db

decks_bp = Blueprint("decks", __name__, url_prefix="/api")

@decks_bp.route("/register_deck", methods=["GET", "POST"])
@jwt_required()
def register_deck():
    db = get_db()

    if request.method == "GET":
        return jsonify({"error": "This endpoint only supports POST requests"}), 405
    
    # Capture json data
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "Invalid or missing token"}), 401
    
    data = request.get_json()
    
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    # Validate user auth
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    
    # Capture deck name
    deck_name = data.get("deck_name")

    # Validate deck_id and match_result
    if not deck_name:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Register into database
    try:
        cursor = db.execute("INSERT INTO decks (deck_name) VALUES (?)", (deck_name,))
        db.commit()

        deck_id = cursor.lastrowid

        deck = db.execute("SELECT id, deck_name FROM decks WHERE id = ?",(deck_id,)).fetchone()
            
        # Relate deck with user
        db.execute("INSERT INTO user_decks (user_id, deck_id) VALUES (?, ?)", (user_id, deck_id))
        db.commit()

        # Message to user
        return jsonify({
            "message": "Deck registered successfully",
            "deck": dict(deck)
            }), 201
    
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    

@decks_bp.route("/decks", methods=["GET"])
@jwt_required()
def get_user_decks():
    db = get_db()
    user_id = get_jwt_identity()

     # Validate user auth
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    
    decks = db.execute("SELECT user_decks.id, decks.deck_name FROM user_decks JOIN decks ON user_decks.deck_id = decks.id WHERE user_decks.user_id = ?;",(user_id,)).fetchall()

    decks_list = [{"id": deck["id"], "deck_name": deck["deck_name"]} for deck in decks]

    return jsonify(decks_list)
