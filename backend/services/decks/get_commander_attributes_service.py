from flask import jsonify

from backend.models.commanders import Commander

def get_commander_attributes_by_id(id):
    commander = Commander.query.get(id)
    if not commander:
        return None
    return commander.to_dict()