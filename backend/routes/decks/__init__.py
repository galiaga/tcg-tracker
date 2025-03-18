from flask import Blueprint

decks_bp = Blueprint("decks", __name__, url_prefix="/api/decks")
