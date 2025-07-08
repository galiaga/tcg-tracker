# backend/routes/player_performance.py

from flask import Blueprint, jsonify, session
from backend.utils.decorators import login_required
from backend import db
from backend.models import LoggedMatch, Deck
from sqlalchemy import func, case, cast, Float, desc
import logging

# --- Constants ---
MIN_MATCHES_FOR_WINNINGEST = 10

# This is the ONLY blueprint this file needs to define.
player_performance_bp = Blueprint(
    "player_performance", 
    __name__, 
    url_prefix="/api"
)

# --- API Endpoint to fetch all summary data ---
@player_performance_bp.route("/performance-summary", methods=["GET"])
@login_required
def get_performance_summary():
    """
    Calculates and returns a comprehensive summary of the user's performance
    across all decks and matches.
    """
    user_id = session.get('user_id')

    try:
        # --- 1. Overall Win Rate & Total Matches ---
        overall_stats = db.session.query(
            func.count(LoggedMatch.id).label('total_matches'),
            func.sum(case((LoggedMatch.result == 0, 1), else_=0)).label('total_wins')
        ).filter(
            LoggedMatch.logger_user_id == user_id,
            LoggedMatch.is_active == True
        ).first()

        total_matches = overall_stats.total_matches or 0
        total_wins = overall_stats.total_wins or 0
        
        if total_matches == 0:
            return jsonify({
                "has_data": False,
                "overall_win_rate": 0,
                "total_matches": 0,
                "winningest_deck": "N/A",
                "most_played_deck": "N/A",
                "turn_order_stats": {}
            })
            
        overall_win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

        # --- 2. Performance by Turn Order (Overall) ---
        turn_order_results = db.session.query(
            LoggedMatch.player_position,
            func.count(LoggedMatch.id).label('matches'),
            func.sum(case((LoggedMatch.result == 0, 1), else_=0)).label('wins')
        ).filter(
            LoggedMatch.logger_user_id == user_id,
            LoggedMatch.is_active == True,
            LoggedMatch.player_position.isnot(None)
        ).group_by(LoggedMatch.player_position).all()
        
        turn_order_stats = {str(i): {"matches": 0, "wins": 0, "win_rate": 0} for i in range(1, 5)}
        for row in turn_order_results:
            pos_key = str(row.player_position)
            win_rate = (row.wins / row.matches * 100) if row.matches > 0 else 0
            turn_order_stats[pos_key] = {
                "matches": row.matches,
                "wins": row.wins,
                "win_rate": round(win_rate, 1)
            }

        # --- 3. Most Played Deck ---
        most_played_deck_query = db.session.query(
            Deck.name,
            func.count(LoggedMatch.id).label('play_count')
        ).join(
            LoggedMatch, Deck.id == LoggedMatch.deck_id
        ).filter(
            LoggedMatch.logger_user_id == user_id,
            LoggedMatch.is_active == True
        ).group_by(Deck.id).order_by(desc('play_count')).first()
        
        most_played_deck = f"{most_played_deck_query.name} ({most_played_deck_query.play_count} plays)" if most_played_deck_query else "N/A"

        # --- 4. Winningest Deck (with minimum matches) ---
        deck_win_rates_subquery = db.session.query(
            LoggedMatch.deck_id,
            (cast(func.sum(case((LoggedMatch.result == 0, 1), else_=0)), Float) * 100 / cast(func.count(LoggedMatch.id), Float)).label('win_rate')
        ).filter(
            LoggedMatch.logger_user_id == user_id,
            LoggedMatch.is_active == True
        ).group_by(LoggedMatch.deck_id).having(
            func.count(LoggedMatch.id) >= MIN_MATCHES_FOR_WINNINGEST
        ).subquery()
        
        winningest_deck_query = db.session.query(
            Deck.name,
            deck_win_rates_subquery.c.win_rate
        ).join(
            deck_win_rates_subquery, Deck.id == deck_win_rates_subquery.c.deck_id
        ).order_by(desc('win_rate')).first()

        winningest_deck = f"{winningest_deck_query.name} ({winningest_deck_query.win_rate:.1f}%)" if winningest_deck_query else "N/A"
        
        response_data = {
            "has_data": True,
            "overall_win_rate": round(overall_win_rate, 1),
            "total_matches": total_matches,
            "winningest_deck": winningest_deck,
            "most_played_deck": most_played_deck,
            "turn_order_stats": turn_order_stats,
        }
        
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error fetching player performance summary for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while calculating performance stats."}), 500