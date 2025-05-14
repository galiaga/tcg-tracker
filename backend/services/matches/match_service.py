# backend/services/matches/match_service.py

from backend import db
from backend.models.logged_match import LoggedMatch, LoggedMatchResult # Updated import
from backend.models.deck import Deck
from sqlalchemy import func, case, Integer, and_, desc, select # Added select
import logging

logger = logging.getLogger(__name__)

# Use Enum for results
RESULT_WIN_ID = LoggedMatchResult.WIN.value

# Service Functions

def get_all_decks_stats(user_id):
    logger.debug(f"Executing get_all_decks_stats for user_id: {user_id}")

    # Explicitly get the Table object for LoggedMatch
    logged_matches_table = LoggedMatch.__table__

    decks_stats = (
        db.session.query(
            Deck.id,
            Deck.name,
            Deck.deck_type_id,
            # ***** USE EXPLICIT TABLE IN CASES *****
            func.sum(case(
                (logged_matches_table.c.is_active == True, 1), # Use table.c.column_name
                else_=0
            )).label("total_matches"),
            func.sum(case(
                (and_(logged_matches_table.c.result == RESULT_WIN_ID, logged_matches_table.c.is_active == True), 1), # Use table.c.column_name
                else_=0
            )).label("total_wins"),
            func.max(case(
                (logged_matches_table.c.is_active == True, logged_matches_table.c.timestamp), # Use table.c.column_name
                else_=None
            )).label("last_match")
            # ***** END EXPLICIT TABLE CASES *****
        )
        .select_from(Deck) # Start from Deck
        # ***** USE EXPLICIT TABLE IN JOIN *****
        .outerjoin(logged_matches_table, and_( # Join using the table object
            logged_matches_table.c.deck_id == Deck.id,
            logged_matches_table.c.logger_user_id == user_id # Ensure matches are logged by the user owning the deck
        ))
        .filter(Deck.user_id == user_id) # Filter decks owned by the user
        .filter(Deck.is_active == True) # Ensure we only process active decks
        .group_by(Deck.id, Deck.name, Deck.deck_type_id)
        .order_by(Deck.name) # Keep ordering by name
        .all()
    )
    logger.debug(f"Query results count for user_id {user_id}: {len(decks_stats)}")

    results = []
    for deck in decks_stats:
        logger.info(f"RAW Query Data for Deck ID {deck.id}: total_matches={deck.total_matches}, total_wins={deck.total_wins}")
        total_matches = int(deck.total_matches or 0)
        total_wins = int(deck.total_wins or 0)
        logger.info(f"[get_all_decks_stats] Deck ID: {deck.id} ('{deck.name}') - total_matches = {total_matches}, total_wins = {total_wins}")
        win_rate = round((total_wins / total_matches) * 100, 2) if total_matches > 0 else 0

        results.append({
            "id": deck.id,
            "name": deck.name,
            "type": deck.deck_type_id,
            "total_matches": total_matches,
            "total_wins": total_wins,
            "win_rate": win_rate,
            "last_match": deck.last_match
        })
    logger.debug(f"Finished processing stats for user_id {user_id}. Returning {len(results)} deck stats.")
    print(f"results: {results}")
    return results

# --- Update get_deck_stats similarly ---

def get_deck_stats(user_id, deck_id):
    """Calculates statistics for a specific active deck (active matches only)."""
    logger.debug(f"Executing get_deck_stats for user_id: {user_id}, deck_id: {deck_id}")

    # Explicitly get the Table object for LoggedMatch
    logged_matches_table = LoggedMatch.__table__

    deck_stats = (
        db.session.query(
            Deck.id,
            Deck.name,
            # ***** USE EXPLICIT TABLE IN CASES *****
            func.sum(case(
                (logged_matches_table.c.is_active == True, 1), # Use table.c.column_name
                else_=0
            )).label("total_matches"),
            func.sum(case(
                (and_(logged_matches_table.c.result == RESULT_WIN_ID, logged_matches_table.c.is_active == True), 1), # Use table.c.column_name
                else_=0
            )).label("total_wins"),
            # ***** END EXPLICIT TABLE CASES *****
        )
        .select_from(Deck) # Start from Deck
        # ***** USE EXPLICIT TABLE IN JOIN *****
        .outerjoin(logged_matches_table, and_( # Join using the table object
            logged_matches_table.c.deck_id == Deck.id,
            logged_matches_table.c.logger_user_id == user_id # Ensure matches are logged by the user
        ))
        .filter(Deck.user_id == user_id, Deck.id == deck_id) # Filter for the specific user and deck
        .filter(Deck.is_active == True) # Ensure the deck itself is active
        .group_by(Deck.id, Deck.name)
        .first()
    )

    # ... (rest of the function remains the same as the previous version) ...

    if deck_stats is None:
        deck_exists = db.session.query(Deck.id).filter_by(id=deck_id, user_id=user_id).first()
        if not deck_exists:
             logger.warning(f"[get_deck_stats] Deck not found or not owned by user_id: {user_id}, deck_id: {deck_id}")
             return None
        target_deck = db.session.query(Deck.id, Deck.name).filter_by(id=deck_id, user_id=user_id, is_active=True).first()
        if not target_deck:
             logger.warning(f"[get_deck_stats] Deck found but is inactive for user_id: {user_id}, deck_id: {deck_id}")
             return None
        logger.info(f"[get_deck_stats] Active deck found but no active matches recorded for user_id: {user_id}, deck_id: {deck_id}")
        return {
            "id": target_deck.id,
            "name": target_deck.name,
            "total_matches": 0,
            "total_wins": 0,
            "win_rate": 0,
        }

    total_matches = int(deck_stats.total_matches or 0)
    total_wins = int(deck_stats.total_wins or 0)
    logger.info(f"[get_deck_stats] Deck ID: {deck_stats.id} ('{deck_stats.name}') - total_matches = {total_matches}, total_wins = {total_wins}")
    win_rate = round((total_wins / total_matches) * 100, 2) if total_matches > 0 else 0

    result_data = {
            "id": deck_stats.id,
            "name": deck_stats.name,
            "total_matches": total_matches,
            "total_wins": total_wins,
            "win_rate": win_rate,
        }
    logger.debug(f"Finished processing stats for user_id {user_id}, deck_id {deck_id}. Returning stats.")
    return result_data