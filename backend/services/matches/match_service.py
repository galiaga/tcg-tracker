# backend/services/matches/match_service.py

from backend import db
from backend.models.match import Match
from backend.models.user_deck import UserDeck
from backend.models.deck import Deck
from sqlalchemy import func, case, Integer, and_
import logging # Import logging

# --- Constants ---
RESULT_WIN_ID = 0
logger = logging.getLogger(__name__) # Setup logger for better practice than print

# --- Aggregation Logic (Counts Active Matches Only) ---
_match_count_case = case(
    (and_(Match.id != None, Match.is_active == True), 1),
    else_=0
)
_win_count_case = case(
    (and_(Match.result == RESULT_WIN_ID, Match.is_active == True), 1),
    else_=0
)

# --- Service Functions ---

def get_all_decks_stats(user_id):
    logger.debug(f"Executing get_all_decks_stats for user_id: {user_id}") # Use logger
    """Calculates statistics for all decks owned by a user (active matches only)."""
    decks_stats = (
        db.session.query(
            Deck.id,
            Deck.name,
            Deck.deck_type_id,
            func.sum(_match_count_case).label("total_matches"),
            func.sum(_win_count_case).label("total_wins"),
            func.max(case((Match.is_active == True, Match.timestamp), else_=None)).label("last_match")
        )
        .select_from(UserDeck)
        .join(Deck, UserDeck.deck_id == Deck.id)
        .outerjoin(Match, Match.user_deck_id == UserDeck.id)
        .filter(UserDeck.user_id == user_id)
        .filter(Deck.is_active == True) # Ensure we only process active decks
        .group_by(Deck.id, Deck.name, Deck.deck_type_id)
        .order_by(Deck.name)
        .all()
    )
    logger.debug(f"Query results count for user_id {user_id}: {len(decks_stats)}")

    results = []
    for deck in decks_stats:
        total_matches = int(deck.total_matches or 0)
        total_wins = int(deck.total_wins or 0)

        # --- PRINT STATEMENT ADDED HERE ---
        # Using logger is generally better than print in applications
        logger.info(f"[get_all_decks_stats] Deck ID: {deck.id} ('{deck.name}') - total_matches = {total_matches}, total_wins = {total_wins}")
        # If you absolutely need print:
        # print(f"[get_all_decks_stats] Deck ID: {deck.id} ('{deck.name}') - total_matches = {total_matches}, total_wins = {total_wins}")

        win_rate = round((total_wins / total_matches) * 100, 2) if total_matches > 0 else 0

        results.append({
            "id": deck.id,
            "name": deck.name,
            "type": deck.deck_type_id,
            "total_matches": total_matches, # This is the value the route will use
            "total_wins": total_wins,
            "win_rate": win_rate,
            "last_match": deck.last_match
        })
    logger.debug(f"Finished processing stats for user_id {user_id}. Returning {len(results)} deck stats.")
    return results

def get_deck_stats(user_id, deck_id):
    logger.debug(f"Executing get_deck_stats for user_id: {user_id}, deck_id: {deck_id}") # Use logger
    """Calculates statistics for a specific deck (active matches only)."""
    deck_stats = (
        db.session.query(
            Deck.id,
            Deck.name,
            func.sum(_match_count_case).cast(Integer).label("total_matches"),
            func.sum(_win_count_case).cast(Integer).label("total_wins"),
        )
        .select_from(UserDeck)
        .join(Deck, UserDeck.deck_id == Deck.id)
        .outerjoin(Match, Match.user_deck_id == UserDeck.id)
        .filter(UserDeck.user_id == user_id, Deck.id == deck_id)
        .filter(Deck.is_active == True) # Ensure the deck itself is active
        .group_by(Deck.id, Deck.name)
        .first()
    )

    if deck_stats is None:
        logger.warning(f"[get_deck_stats] No active deck or matches found for user_id: {user_id}, deck_id: {deck_id}")
        return None

    total_matches = int(deck_stats.total_matches or 0)
    total_wins = int(deck_stats.total_wins or 0)

    # --- PRINT STATEMENT ADDED HERE ---
    # Using logger is generally better than print in applications
    logger.info(f"[get_deck_stats] Deck ID: {deck_stats.id} ('{deck_stats.name}') - total_matches = {total_matches}, total_wins = {total_wins}")
    # If you absolutely need print:
    # print(f"[get_deck_stats] Deck ID: {deck_stats.id} ('{deck_stats.name}') - total_matches = {total_matches}, total_wins = {total_wins}")

    win_rate = round((total_wins / total_matches) * 100, 2) if total_matches > 0 else 0

    result_data = {
            "id": deck_stats.id,
            "name": deck_stats.name,
            "total_matches": total_matches, # This is the value the route will use
            "total_wins": total_wins,
            "win_rate": win_rate,
        }
    logger.debug(f"Finished processing stats for user_id {user_id}, deck_id {deck_id}. Returning stats.")
    return result_data