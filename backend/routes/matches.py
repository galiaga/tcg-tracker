from flask import Flask, jsonify, Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import get_db

matches_bp = Blueprint("matches", __name__, url_prefix="/api")

@matches_bp.route("/log_match", methods=["GET", "POST"])
@jwt_required()
def log_match():
    db = get_db()

    if request.method == "GET":
        return jsonify({"error": "This endpoint only supports POST requests"}), 405

    # Capture json data
    user_id = get_jwt_identity()
    data = request.get_json()
    deck_id = data.get("deck_id")
    match_result = data.get("match_result")

    # Validate user auth
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    
    # Retrieve user decks
    decks = db.execute("SELECT user_decks.id, decks.deck_name FROM user_decks JOIN decks ON user_decks.deck_id = decks.id WHERE user_decks.user_id = ?;",(g.user_id,)).fetchall()
 
    # Validate deck_id and match_result
    if not deck_id or match_result is None:
        return jsonify({"error": "Missing required fields"}), 400
        
    # Register into database
    try:
        cursor = db.execute("INSERT INTO matches (result, user_deck_id) VALUES (?, ?)", (match_result, deck_id))
        db.commit()

        match_id = cursor.lastrowid
        
        match = db.execute("SELECT id, result, user_deck_id FROM matches WHERE id = ?",(match_id,)).fetchone()

        return jsonify({
            "message": "Match logged successfully",
            "match": dict(match)
            }), 201
    
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    