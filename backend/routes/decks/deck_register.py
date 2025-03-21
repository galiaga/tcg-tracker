<<<<<<< HEAD
from flask import Blueprint, jsonify, request, Response
=======
from flask import Blueprint, jsonify, request
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.models.user import User
from backend.models.deck import Deck
from backend.models.user_deck import UserDeck
from backend.models.commander_deck import CommanderDeck
<<<<<<< HEAD
import json
=======
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822

deck_register_bp = Blueprint("deck_register", __name__, url_prefix="/api")

COMMANDER_DECK_TYPE_ID = 7

@deck_register_bp.route("/register_deck", methods=["POST"])
@jwt_required()
def register_deck():
<<<<<<< HEAD
=======
    # Aquí el código original de register_deck
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822
    if request.method == "GET":
        return jsonify({"error": "This endpoint only supports POST requests"}), 405

    user_id = get_jwt_identity()
<<<<<<< HEAD
    data = request.get_json()
    print(data)
    deck_name = data.get("deck_name")
    deck_type_id = data.get("deck_type")

=======
    print(f"🔹 user_id obtenido desde JWT: {user_id}")
    data = request.get_json()
    deck_name = data.get("deck_name")
    deck_type_id = data.get("deck_type")

    # Convert deck_type_id to int
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822
    try:
        deck_type_id = int(deck_type_id)
    except ValueError:
        pass

    commander_id = data.get("commander_id")
<<<<<<< HEAD
    partner_id = data.get("partner_id")
    friends_forever_id = data.get("friends_forever_id")
    doctor_companion_id = data.get("doctor_companion_id")
    time_lord_doctor_id = data.get("time_lord_doctor_id")
=======
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    if not deck_name:
<<<<<<< HEAD
        return jsonify({"error": "Add a Deck Name"}), 400
    if (deck_type_id == COMMANDER_DECK_TYPE_ID) and not commander_id:
        return jsonify({"error": "Add your Commander"}), 400
    
    from backend.models import Commander
    commander = db.session.get(Commander, commander_id)

    if commander and commander.partner and not partner_id:
        return jsonify({"error": "This Commander requires a Partner."}), 400
    
    if commander and commander.friends_forever and not friends_forever_id:
        return jsonify({"error": "This Commander requires another Friend Forever Commander."}), 400
    
    if commander and commander.doctor_companion and not time_lord_doctor_id:
        return jsonify({"error": "This Doctor's Companion requires a Time Lord Doctor Commander."}), 400
    
    if commander and commander.time_lord_doctor and not doctor_companion_id:
        return jsonify({"error": "This Doctor requires a Doctor's Companion Commander."}), 400
=======
        return jsonify({"error": "Missing required fields"}), 400
    if (deck_type_id == COMMANDER_DECK_TYPE_ID) and not commander_id:
        return jsonify({"error": "Commander ID is required for Commander decks"}), 400
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822
    
    try:
        new_deck = Deck(user_id=user_id, name=deck_name, deck_type_id=deck_type_id)
        db.session.add(new_deck)
        db.session.commit()

        user_deck = UserDeck(user_id=user_id, deck_id=new_deck.id)
        db.session.add(user_deck)
<<<<<<< HEAD

        associations = {
            "partner_id": partner_id,
            "friends_forever_id": friends_forever_id,
            "time_lord_doctor_id": time_lord_doctor_id,
            "doctor_companion_id": doctor_companion_id
        }

        non_null_associations = {key: value for key, value in associations.items() if value is not None}

        if len(non_null_associations) > 1:
            return jsonify({
                "error": "Only one of partner_id, friends_forever_id, doctor_companion_id or time_lord_doctor_id can be included."
            }), 400
        
        if commander_id:
            associated_commander_id = next(iter(non_null_associations.values()), None)

            if associated_commander_id and str(commander_id) == str(associated_commander_id):
                return jsonify({"error": "Commander and associated Commander cannot be the same."}), 400
            
            VALIDATION_RULES = {
                "partner_id": lambda c: c.partner,
                "friends_forever_id": lambda c: c.friends_forever,
                "time_lord_doctor_id": lambda c: c.time_lord_doctor,
                "doctor_companion_id": lambda c: c.doctor_companion
            }

            if associated_commander_id:
                assoc_key = next(iter(non_null_associations))
                associated_commander = db.session.get(Commander, associated_commander_id)

                if not associated_commander:
                    return jsonify({"error": "Associated Commander not found."}), 404

                if not VALIDATION_RULES[assoc_key](associated_commander):
                    label = assoc_key.replace("_id", "").replace("_", " ").title()
                    return jsonify({"error": f"{associated_commander.name} is not a valid {label}."}), 400

            commander_deck = CommanderDeck(
                deck_id=new_deck.id,
                commander_id=commander_id,
                associated_commander_id=associated_commander_id
            )
=======
        
        if commander_id:
            commander_deck = CommanderDeck(deck_id=new_deck.id, commander_id=commander_id)
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822
            db.session.add(commander_deck)

        db.session.commit()

<<<<<<< HEAD
        return Response(
            json.dumps({
                "message": "Deck registered successfully",
                "deck": {
                    "id": new_deck.id,
                    "name": new_deck.name,
                    "deck_type": deck_type_id,
                    "commander_id": commander_id,
                    "partner_id": partner_id,
                    "friends_forever_id": friends_forever_id,
                    "doctor_companion_id": doctor_companion_id,
                    "time_lord_doctor_id": time_lord_doctor_id
                }
            }, indent=4),  # Formato legible
            mimetype="application/json",
            status=201
        )
=======
        return jsonify({
            "message": "Deck registered successfully",
            "deck": {
                "id": new_deck.id,
                "name": new_deck.name,
                "deck_type": deck_type_id,
                "commander_id": commander_id
            }
        }), 201
>>>>>>> 6e48b3a047b3fec03eac240a8a1d934082a59822

    except Exception as e:
        db.session.rollback()
        print(f"❌ Database error: {e}") 
        return jsonify({"error": "Database error", "details": str(e)}), 500