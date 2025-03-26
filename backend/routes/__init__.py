from flask import Blueprint

from backend.routes.decks import decks_bp
from backend.routes.decks.deck_register import deck_register_bp
from backend.routes.decks.deck_details import deck_details_bp

def register_routes(app):
    app.register_blueprint(decks_bp)
    app.register_blueprint(deck_register_bp)
    app.register_blueprint(deck_details_bp)