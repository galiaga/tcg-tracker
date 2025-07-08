# In a service file, e.g., backend/services/deck/deck_service.py
# Define a function to get mulligan stats for a specific deck
# This function will query the database for matches related to the deck and calculate win rates based on mulligan counts.
# Ensure you have the necessary imports and database setup in your Flask app.
# backend/services/decks/deck_service.py

from sqlalchemy import func, case
from backend.models import LoggedMatch, Deck
from backend import db

def get_mulligan_stats_for_deck(deck_id: int, user_id: int):
    """
    Calculates win rate statistics grouped by the number of mulligans for a specific deck.
    """
    # First, ensure the deck belongs to the user
    deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()
    if not deck:
        return None # Or raise an exception

    # Define the labels for each mulligan value
    mulligan_label = case(
        (LoggedMatch.player_mulligans == -1, 'Free (to 7)'),
        (LoggedMatch.player_mulligans == 0, 'Keep First 7'),
        # For other values, create a dynamic label like "To 6 (1)"
        else_=func.concat('To ', 7 - LoggedMatch.player_mulligans, ' (', LoggedMatch.player_mulligans, ')')
    )

    # The main query
    mulligan_stats_query = db.session.query(
        LoggedMatch.player_mulligans,
        mulligan_label.label('label'),
        func.count(LoggedMatch.id).label('game_count'),
        # Sum up wins (where result is 0)
        func.sum(case((LoggedMatch.result == 0, 1), else_=0)).label('win_count')
    ).filter(
        LoggedMatch.deck_id == deck_id,
        LoggedMatch.is_active == True,
        LoggedMatch.player_mulligans.isnot(None) # Only include matches where mulligans were logged
    ).group_by(
        LoggedMatch.player_mulligans
    ).order_by(
        # Order logically: Free, Keep 7, then ascending mulligans
        case(
            (LoggedMatch.player_mulligans == -1, -1),
            (LoggedMatch.player_mulligans == 0, 0),
            else_=LoggedMatch.player_mulligans
        )
    )

    results = mulligan_stats_query.all()

    # Process results into a clean list of dictionaries
    stats = []
    for row in results:
        win_rate = (row.win_count / row.game_count * 100) if row.game_count > 0 else 0
        stats.append({
            'label': row.label,
            'game_count': row.game_count,
            'win_count': row.win_count,
            'win_rate': round(win_rate, 1)
        })

    return stats