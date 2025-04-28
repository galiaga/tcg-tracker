from flask import Blueprint, jsonify
from backend.utils.decorators import login_required
from backend import db, limiter
from backend.models.deck_type import DeckType

deck_types_bp = Blueprint('deck_types', __name__)

# Retrieve deck types
@deck_types_bp.route('/deck_types', methods=['GET'])
@limiter.limit("60 per minute")
@login_required
def get_deck_types():
    deck_types = DeckType.query.all()
    return jsonify([{'id': dt.id, 'deck_type': dt.name} for dt in deck_types])
