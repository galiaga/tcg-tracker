from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pprint import pprint

from backend.database import db
from backend.models.commanders import Commander

commanders_bp = Blueprint("commanders", __name__, url_prefix="/api")

# Search commanders in the local database based on user input
@commanders_bp.route("/search_commanders", methods=["GET"])
def search_commanders():
    query = request.args.get("q", "").strip().lower()

    relation_type = request.args.get("type", "").lower()

    if not query:
        return jsonify([])

    if relation_type == "partner":
        commanders = Commander.query.filter(Commander.partner == 1, Commander.name.ilike(f"{query}%")).all()
        print(f"Comandantes encontrados (partner): {commanders}")
        pprint([commander.name for commander in commanders])
    elif relation_type == "friendsForever":
        commanders = Commander.query.filter(Commander.friends_forever == 1, Commander.name.ilike(f"{query}%")).all()
        print(f"Comandantes encontrados (friends forever): {commanders}")
        pprint([commander.name for commander in commanders])
    elif relation_type == "doctorCompanion":
        commanders = Commander.query.filter(Commander.time_lord_doctor == 1, Commander.name.ilike(f"{query}%")).all()
        print(f"Comandantes encontrados (time_lord_doctor): {commanders}")
        pprint([commander.name for commander in commanders])
    elif relation_type == "timeLordDoctor":
        commanders = Commander.query.filter(Commander.doctor_companion == 1, Commander.name.ilike(f"{query}%")).all()
        print(f"Comandantes encontrados (doctor companion): {commanders}")
        pprint([commander.name for commander in commanders])
    else:
        commanders = Commander.query.filter(Commander.name.ilike(f"{query}%")).all()
        print(f"Comandantes encontrados (todos): {commanders}")
        pprint([commander.name for commander in commanders])

    return jsonify([{
        "id": c.id,
        "name": c.name
    } for c in commanders])

@commanders_bp.route("/get_commander_attributes", methods=["GET"])
@jwt_required()
def get_commander_attributes():
    print("HEY")
    q = request.args.get("q")

    if not q:
        return jsonify({"error": "Missing parameter 'q'"}), 400
    
    try:
        commander_id = int(q)
    except ValueError:
        return jsonify({"error": "'q' must be a valid integer"}), 422
    
    commander = Commander.query.get(commander_id)

    if not commander:
        return jsonify({"error": "Commander not found"}), 404

    return jsonify(commander.to_dict()) 