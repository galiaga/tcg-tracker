from flask import Blueprint, jsonify, request
from backend.database import db
from backend.models.commanders import Commander

commanders_bp = Blueprint("commanders", __name__, url_prefix="/api")

# Search commanders in the local database based on user input
@commanders_bp.route("/search_commanders", methods=["GET"])
def search_commanders():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify([])

    commanders = Commander.query.filter(Commander.name.ilike(f"{query}%")).all()

    return jsonify([{
        "id": c.id,
        "name": c.name
    } for c in commanders])
