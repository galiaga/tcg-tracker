from flask import Blueprint, jsonify, request, session
from sqlalchemy.orm import selectinload
from backend.utils.decorators import login_required
from backend import db, limiter
from backend.models.tag import Tag
from backend.models.deck import Deck
from sqlalchemy.exc import IntegrityError

tags_bp = Blueprint('tags', __name__, url_prefix='/api')

@tags_bp.route('/tags', methods=['GET'])
@limiter.limit("60 per minute")
@login_required
def get_user_tags():
    current_user_id = session.get('user_id')
    user_tags = Tag.query.filter_by(user_id=current_user_id).order_by(Tag.name).all()
    tags_list = [{'id': tag.id, 'name': tag.name} for tag in user_tags]
    return jsonify(tags_list)

@tags_bp.route('/tags', methods=['POST'])
@limiter.limit("60 per minute")
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
    
@tags_bp.route('/decks/<int:deck_id>/tags', methods=['POST'])
@limiter.limit("60 per minute")
@login_required
def add_tag_to_deck(deck_id):
    current_user_id = session.get('user_id')
    data = request.get_json()
    if not data or 'tag_id' not in data: return jsonify({"error": "Missing 'tag_id' in request body"}), 400
    
    try:
        tag_id = int(data.get('tag_id'))
    except (ValueError, TypeError):
        return jsonify({"error": "'tag_id' must be a valid integer"}), 400

    deck = Deck.query.options(selectinload(Deck.tags)).filter_by(id=deck_id, user_id=current_user_id, is_active=True).first()
    if not deck: return jsonify({"error": "Active deck not found or not owned by user"}), 404

    tag_to_add = db.session.get(Tag, tag_id)
    if not tag_to_add or tag_to_add.user_id != current_user_id: return jsonify({"error": "Tag not found or not owned by user"}), 404
    if tag_to_add in deck.tags: return jsonify({"message": "Tag already associated with this deck"}), 200

    try:
        deck.tags.append(tag_to_add)
        db.session.commit()
        return jsonify({"message": "Tag associated successfully"}), 201
    except Exception as e:
        db.session.rollback()
        # logger.error(f"Error adding tag {tag_id} to deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while associating the tag"}), 500

@tags_bp.route('/decks/<int:deck_id>/tags/<int:tag_id>', methods=['DELETE'])
@limiter.limit("60 per minute")
@login_required
def remove_tag_from_deck(deck_id, tag_id):
    current_user_id = session.get('user_id')
    deck = Deck.query.options(selectinload(Deck.tags)).filter_by(id=deck_id, user_id=current_user_id, is_active=True).first()
    if not deck: return jsonify({"error": "Active deck not found or not owned by user"}), 404

    tag_to_remove = db.session.get(Tag, tag_id)
    if not tag_to_remove or tag_to_remove.user_id != current_user_id: return jsonify({"error": "Tag not found or not owned by user"}), 404
    if tag_to_remove not in deck.tags: return jsonify({"error": "Tag is not associated with this deck"}), 404

    try:
        deck.tags.remove(tag_to_remove)
        db.session.commit()
        return '', 204 # Standard for successful DELETE with no content
    except Exception as e:
        db.session.rollback()
        # logger.error(f"Error removing tag {tag_id} from deck {deck_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while disassociating the tag"}), 500