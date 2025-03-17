from flask import Blueprint, jsonify, request
from backend.database import get_db

commanders_bp = Blueprint("commanders", __name__, url_prefix="/api")

@commanders_bp.route("/search_commanders", methods=["GET"])
def search_commanders():
    """Search commanders in the local database based on user input."""
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify([])

    db = get_db()
    commanders = db.execute("""
        SELECT id, name, mana_cost, type_line, oracle_text, colors, color_identity, image_url 
        FROM commanders WHERE name LIKE ? ORDER BY name LIMIT 10
    """, (query + "%",)).fetchall()

    return jsonify([{
        "id": c["id"],
        "name": c["name"],
        "mana_cost": c["mana_cost"],
        "type_line": c["type_line"],
        "oracle_text": c["oracle_text"],
        "colors": c["colors"],
        "color_identity": c["color_identity"],
        "image_url": c["image_url"]
    } for c in commanders])
