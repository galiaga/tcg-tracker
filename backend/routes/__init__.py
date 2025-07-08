from backend.routes.decks import decks_bp
from backend.routes.auth import auth_bp
from backend.routes.frontend import frontend_bp
from backend.routes.matches import matches_bp
from backend.routes.deck_types import deck_types_bp
from backend.routes.decks import decks_bp
from backend.routes.commanders import commanders_bp
from backend.routes.match_history import matches_history_bp
from backend.routes.tags import tags_bp
from backend.routes.player_performance import player_performance_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(decks_bp)
    app.register_blueprint(deck_types_bp, url_prefix='/api')
    app.register_blueprint(commanders_bp, url_prefix='/api')
    app.register_blueprint(matches_history_bp, url_prefix='/api')
    app.register_blueprint(tags_bp, url_prefix='/api')
    app.register_blueprint(player_performance_bp)
