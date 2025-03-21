from flask import jsonify

from backend.models.commanders import Commander

def get_commander_attributes_by_id(id):
    print(f"get_commander_attributes_by_id = {id}")
    commander = Commander.query.get(id)

    if not commander:
        return jsonify({"error": "Commander not found"}), 404

    print(vars(commander))
    commander_attributes = jsonify(commander.to_dict())
    print(commander_attributes)
    return commander_attributes
