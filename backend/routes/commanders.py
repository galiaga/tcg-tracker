from flask import Blueprint, jsonify, request
from sqlalchemy import select, true
from pprint import pprint

from backend import db
from backend.utils.decorators import login_required
from backend.models.commanders import Commander

commanders_bp = Blueprint("commanders", __name__, url_prefix="/api")

@commanders_bp.route("/search_commanders", methods=["GET"])
def search_commanders():
    query = request.args.get("q", "").strip().lower()
    relation_type = request.args.get("type", "").lower()

    if not query:
        return jsonify([])

    stmt = select(Commander)

    if relation_type == "partner":
        stmt = stmt.where(Commander.partner == true(), Commander.name.ilike(f"{query}%"))
    elif relation_type == "friendsforever":
        stmt = stmt.where(Commander.friends_forever == true(), Commander.name.ilike(f"{query}%"))
    elif relation_type == "doctorcompanion":
        stmt = stmt.where(Commander.time_lord_doctor == true(), Commander.name.ilike(f"{query}%"))
    elif relation_type == "timelorddoctor":
        stmt = stmt.where(Commander.doctor_companion == true(), Commander.name.ilike(f"{query}%"))
    elif relation_type == "background":
        stmt = stmt.where(Commander.choose_a_background == true(), Commander.name.ilike(f"{query}%"))
    elif relation_type == "chooseabackground":
        stmt = stmt.where(Commander.background == true(), Commander.name.ilike(f"{query}%"))
    else:
        stmt = stmt.where(Commander.name.ilike(f"{query}%"))

    commanders = db.session.scalars(stmt).all()

    return jsonify([{
        "id": c.id,
        "name": c.name,
        "image": c.art_crop if c.art_crop else c.image_url
    } for c in commanders])


@commanders_bp.route("/get_commander_attributes", methods=["GET"])
@login_required
def get_commander_attributes():
    q = request.args.get("q")

    if not q:
        return jsonify({"error": "Missing parameter 'q'"}), 400

    try:
        commander_id = int(q)
    except ValueError:
        return jsonify({"error": "'q' must be a valid integer"}), 422

    commander = db.session.get(Commander, commander_id)

    if not commander:
        return jsonify({"error": "Commander not found"}), 404

    return jsonify(commander.to_dict())