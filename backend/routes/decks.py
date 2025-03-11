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

    # Validación de usuario y datos
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    if not deck_name:
        return jsonify({"error": "Missing required fields"}), 400

    # Obtener username desde la BD
    user = db.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    username = user["username"] if user else "Unknown"

    # Registrar deck en la BD
    try:
        cursor = db.execute("INSERT INTO decks (deck_name) VALUES (?)", (deck_name,))
        db.commit()
        deck_id = cursor.lastrowid

        # Relacionar deck con el usuario
        db.execute("INSERT INTO user_decks (user_id, deck_id) VALUES (?, ?)", (user_id, deck_id))
        db.commit()

        # Responder con el username y deck registrado
        return jsonify({
            "message": "Deck registered successfully",
            "deck": {"id": deck_id, "name": deck_name},
            "username": username  # 🔹 Se incluye el username en la respuesta
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
