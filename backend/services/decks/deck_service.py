# backend/services/decks/deck_service.py

from sqlalchemy import func, case, literal, Integer, select, Text, text
from backend.models import LoggedMatch, Deck, Commander, OpponentCommanderInMatch
from backend import db

MIN_ENCOUNTERS_FOR_MATCHUP = 3

def get_deck_matchup_stats(deck_id: int, deck_average_wr: float):
    """
    Calculates win rates against specific opponent command zones.
    
    This definitive version uses a raw SQL subquery for creating the opponent
    signatures. This is necessary to bypass a persistent SQLAlchemy compiler
    issue. The raw SQL is known to be correct and performant.
    """

    # Step 1: Define the raw SQL and describe its output columns to SQLAlchemy.
    # This is the correct pattern for creating a selectable from raw text.
    opponent_signatures_subquery = text("""
        SELECT
            ocim.logged_match_id,
            string_agg(c.name, ' / ' ORDER BY c.name ASC) AS opponent_signature
        FROM opponent_commanders_in_match ocim
        JOIN commanders c ON ocim.commander_id = c.id
        GROUP BY ocim.logged_match_id, ocim.seat_number
    """).columns(
        logged_match_id=Integer,
        opponent_signature=Text
    ).subquery("opponent_signatures")

    # Step 2: Join the main SQLAlchemy query to this raw SQL subquery.
    # The rest of the query can still be built using the ORM.
    matchup_stats_query = db.session.query(
        opponent_signatures_subquery.c.opponent_signature,
        func.count().label('games'),
        func.sum(case((LoggedMatch.result == 0, 1), else_=0)).label('wins')
    ).select_from(LoggedMatch).join(
        opponent_signatures_subquery,
        LoggedMatch.id == opponent_signatures_subquery.c.logged_match_id
    ).filter(
        LoggedMatch.deck_id == deck_id,
        LoggedMatch.is_active == True
    ).group_by(
        opponent_signatures_subquery.c.opponent_signature
    ).having(
        func.count() >= MIN_ENCOUNTERS_FOR_MATCHUP
    ).all()

    # Process and Partition the results (this logic is correct and remains unchanged)
    nemesis_candidates, favorable_candidates = [], []
    for row in matchup_stats_query:
        win_rate = (row.wins / row.games * 100) if row.games > 0 else 0
        matchup = {
            "name": row.opponent_signature, "wins": row.wins, "losses": row.games - row.wins,
            "win_rate": round(win_rate, 1)
        }
        if win_rate < deck_average_wr:
            nemesis_candidates.append(matchup)
        elif win_rate > deck_average_wr:
            favorable_candidates.append(matchup)

    nemesis_matchups = sorted(nemesis_candidates, key=lambda x: x['win_rate'])[:5]
    favorable_matchups = sorted(favorable_candidates, key=lambda x: x['win_rate'], reverse=True)[:5]

    return {"nemesis": nemesis_matchups, "favorable": favorable_matchups}

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