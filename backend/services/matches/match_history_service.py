# backend/services/matches/match_history_service.py

from sqlalchemy.orm import selectinload
from backend import db
# --- MODIFIED IMPORTS ---
from backend.models import LoggedMatch, Deck, DeckType, Tag
# We no longer need OpponentCommanderInMatch or Commander here directly
from sqlalchemy import desc, text, Integer
from sqlalchemy.dialects.postgresql import JSONB # Use JSONB for efficiency
# --- END MODIFIED IMPORTS ---
import logging

logger = logging.getLogger(__name__)

def get_matches_by_user(user_id, deck_id=None, limit=None, offset=None, tag_ids=None):
    """
    Fetches match history for a user, enriching it with opponent data using a robust
    raw SQL subquery to prevent ORM compiler issues.
    """
    
    # --- THE ROBUST SOLUTION: A SINGLE RAW SQL SUBQUERY ---
    # This subquery does all the complex work in pure, reliable SQL:
    # 1. Inner query: Groups commanders by match and seat to create "signatures" (e.g., 'Tymna / Kraum').
    # 2. Outer query: Aggregates these signatures into a single JSON array for each match ID.
    # This completely bypasses the SQLAlchemy ORM compiler for the complex aggregation part.
    aggregated_opponents_subquery = text("""
        SELECT
            sub.logged_match_id,
            jsonb_agg(sub.signature) AS opponents
        FROM (
            SELECT
                ocim.logged_match_id,
                string_agg(c.name, ' / ' ORDER BY c.name ASC) AS signature
            FROM opponent_commanders_in_match ocim
            JOIN commanders c ON ocim.commander_id = c.id
            GROUP BY ocim.logged_match_id, ocim.seat_number
        ) AS sub
        GROUP BY sub.logged_match_id
    """).columns(
        logged_match_id=Integer,
        opponents=JSONB  # Define the output columns and their types
    ).subquery("aggregated_opponents")

    # --- SIMPLIFIED MAIN QUERY ---
    # Now we build a simple ORM query and just join our pre-computed subquery.
    query_builder = (
        db.session.query(
            LoggedMatch,
            Deck,
            DeckType,
            aggregated_opponents_subquery.c.opponents # Select the 'opponents' column from our subquery
        )
        .options(selectinload(LoggedMatch.tags))
        .select_from(LoggedMatch)
        .join(Deck, LoggedMatch.deck_id == Deck.id)
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        # Use a simple outer join on our robust, raw SQL subquery
        .outerjoin(
            aggregated_opponents_subquery, 
            LoggedMatch.id == aggregated_opponents_subquery.c.logged_match_id
        )
        .filter(LoggedMatch.logger_user_id == user_id)
        .filter(LoggedMatch.is_active == True)
        .filter(Deck.is_active == True)
    )
    # --- END SIMPLIFIED MAIN QUERY ---

    # --- OPTIONAL FILTERS, ORDERING, PAGINATION (All Unchanged) ---
    if deck_id is not None:
        query_builder = query_builder.filter(Deck.id == deck_id)

    if tag_ids:
        query_builder = query_builder.filter(LoggedMatch.tags.any(Tag.id.in_(tag_ids)))

    query_builder = query_builder.order_by(desc(LoggedMatch.timestamp))

    if limit is not None and limit > 0:
        current_offset = offset if (offset is not None and offset >= 0) else 0
        query_builder = query_builder.limit(limit).offset(current_offset)

    results = query_builder.all()

    return results