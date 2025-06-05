from flask import Blueprint, jsonify, request
from sqlalchemy import select, true, or_
# from pprint import pprint # Not strictly needed unless for deeper debugging

from backend import db, limiter 
from backend.utils.decorators import login_required 
from backend.models.commanders import Commander

commanders_bp = Blueprint("commanders_api", __name__, url_prefix="/api")

ROLE_PARTNER = "partner"
ROLE_FRIENDS_FOREVER = "friends_forever"
ROLE_BACKGROUND = "background" 
ROLE_CHOOSE_A_BACKGROUND = "choose_a_background" 
ROLE_DOCTOR_COMPANION = "doctor_companion" 
ROLE_TIME_LORD_DOCTOR = "time_lord_doctor"   

@commanders_bp.route("/search_commanders", methods=["GET"])
def search_commanders_route(): 
    query = request.args.get("q", "").strip() 
    relation_type = request.args.get("type", None) 

    if not query or len(query) < 1: 
        return jsonify([])

    # Ensure all necessary columns for the response are selected
    stmt = select(
        Commander.id, 
        Commander.name, 
        Commander.image_url, # Explicitly select image_url
        Commander.art_crop   # Explicitly select art_crop
        # Add boolean flags if they are needed by frontend logic for pairing,
        # but they are not used in the current jsonify list comprehension.
        # Commander.partner, Commander.friends_forever, Commander.background,
        # Commander.choose_a_background, Commander.doctor_companion, Commander.time_lord_doctor
    ).where(Commander.name.ilike(f"%{query}%"))

    if relation_type:
        relation_type = relation_type.lower()
        if relation_type == ROLE_PARTNER:
            stmt = stmt.where(Commander.partner == true())
        elif relation_type == ROLE_FRIENDS_FOREVER:
            stmt = stmt.where(Commander.friends_forever == true())
        elif relation_type == ROLE_BACKGROUND: 
            stmt = stmt.where(Commander.background == true())
        elif relation_type == ROLE_CHOOSE_A_BACKGROUND: 
            stmt = stmt.where(Commander.background == true()) 
        elif relation_type == ROLE_DOCTOR_COMPANION: 
            stmt = stmt.where(Commander.doctor_companion == true())
        elif relation_type == ROLE_TIME_LORD_DOCTOR: 
            stmt = stmt.where(Commander.time_lord_doctor == true())
    
    stmt = stmt.order_by(Commander.name).limit(20) 
    
    commanders_results = db.session.execute(stmt).mappings().all()

    # Debugging: Print the keys of the first result to confirm selected columns
    if commanders_results:
        print(f"Debug: First commander result keys: {commanders_results[0].keys()}")
        # print(f"Debug: First commander result data: {dict(commanders_results[0])}")


    # Construct the response using .get() for safety, though keys should exist if selected
    response_data = []
    for c_mapping in commanders_results:
        response_data.append({
            "id": c_mapping.id, # Or c_mapping.get('id')
            "name": c_mapping.name, # Or c_mapping.get('name')
            # Use .get() with a fallback to handle potential None for art_crop more cleanly
            "image_url": c_mapping.get('art_crop') if c_mapping.get('art_crop') else c_mapping.get('image_url')
        })

    return jsonify(response_data)


@commanders_bp.route("/get_commander_attributes", methods=["GET"])
@limiter.limit("60 per minute")
@login_required
def get_commander_attributes_route(): 
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