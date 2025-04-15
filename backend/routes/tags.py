from flask import Blueprint, jsonify, request, session
from backend.utils.decorators import login_required
from backend import db
from backend.models.tag import Tag
from sqlalchemy.exc import IntegrityError

tags_bp = Blueprint('tags', __name__, url_prefix='/api')

@tags_bp.route('/tags', methods=['GET'])
@login_required
def get_user_tags():
    current_user_id = session.get('user_id')
    user_tags = Tag.query.filter_by(user_id=current_user_id).order_by(Tag.name).all()
    tags_list = [{'id': tag.id, 'name': tag.name} for tag in user_tags]
    return jsonify(tags_list)

@tags_bp.route('/tags', methods=['POST'])
@login_required
def create_user_tag():
    current_user_id = session.get('user_id')
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({"error": "Missing 'name' in request body"}), 400

    tag_name = data['name']
    if not isinstance(tag_name, str) or not tag_name.strip():
         return jsonify({"error": "Tag name must be a non-empty string"}), 400

    normalized_name = tag_name.strip().lower()
    if not normalized_name:
         return jsonify({"error": "Tag name cannot be empty after stripping whitespace"}), 400

    existing_tag = Tag.query.filter_by(user_id=current_user_id, name=normalized_name).first()

    if existing_tag:
        return jsonify({"error": "Tag already exists"}), 409

    new_tag = Tag(user_id=current_user_id, name=normalized_name)

    try:
        db.session.add(new_tag)
        db.session.commit()
        return jsonify({'id': new_tag.id, 'name': new_tag.name}), 201
    except IntegrityError as e:
        db.session.rollback()
        if 'uq_user_tag_name' in str(e.orig):
             return jsonify({"error": "Tag already exists (concurrent creation likely)"}), 409
        else:
            print(f"Database Integrity Error: {e}") 
            return jsonify({"error": "Database error creating tag"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"Error creating tag: {e}") 
        return jsonify({"error": "An unexpected error occurred"}), 500