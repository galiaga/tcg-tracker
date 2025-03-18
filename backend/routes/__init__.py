from flask import Blueprint

from backend.routes.decks import decks_bp

def register_routes(app):
    app.register_blueprint(decks_bp)