from flask import Flask, jsonify, Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.models.match import Match

matches_bp = Blueprint("matches", __name__, url_prefix="/api")

@matches_bp.route("/log_match", methods=["GET", "POST"])
@jwt_required()
def log_match():

    if request.method == "GET":
        return jsonify({"error": "This endpoint only supports POST requests"}), 405

    # Capture json data
    user_id = get_jwt_identity()
    data = request.get_json()
    deck_id = data.get("deck_id")
    match_result = data.get("match_result")
    print(data)

    # Validate user auth
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
 
    # Validate deck_id and match_result
    if not deck_id or match_result is None:
        return jsonify({"error": "Missing required fields"}), 400
        
    # Register into database
    try:
        new_match = Match(result=match_result, user_deck_id=deck_id)
        db.session.add(new_match)
        db.session.commit()

        return jsonify({
            "message": "Match logged successfully",
            "match": {
                "id": new_match.id,
                "name": new_match.timestamp,
                "result": new_match.result,
                "user_deck_id": new_match.user_deck_id
            }
            }), 201
    
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    