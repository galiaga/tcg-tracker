# backend/services/matches/match_history_service.py

from sqlalchemy.orm import selectinload
from backend import db
# Ensure all required models are imported - REMOVED UserDeck
from backend.models import LoggedMatch, Deck, DeckType, Tag
from sqlalchemy import desc
import logging # Import logging

# Add print statement for debugging load issues
print("!!! EXECUTING LATEST match_history_service.py CODE !!!", flush=True)
logger = logging.getLogger(__name__)

def get_matches_by_user(user_id, deck_id=None, limit=None, offset=None, tag_ids=None):
    """
    Fetches match history logged by a user, returning only matches that are active
    AND associated with an active deck.

    Args:
        user_id (int): The ID of the user whose logged matches to fetch.
        deck_id (int, optional): Filter matches by a specific deck ID used in the match. Defaults to None.
        limit (int, optional): Maximum number of matches to return. Defaults to None.
        offset (int, optional): Number of matches to skip. Defaults to None.
        tag_ids (list[int], optional): Filter matches by associated tag IDs. Defaults to None.

    Returns:
        List[Tuple[LoggedMatch, Deck, DeckType]]: A list of tuples containing the
                                            LoggedMatch, associated Deck, and DeckType objects.
    """
    logger.debug(f"Executing get_matches_by_user for user_id: {user_id}, deck_id: {deck_id}, tags: {tag_ids}, limit: {limit}, offset: {offset}")

    # Start building the query, selecting the necessary objects
    query_builder = (
        db.session.query(
            LoggedMatch,
            Deck,
            DeckType
        )
        # Eager load tags for each match to prevent N+1 queries later
        .options(selectinload(LoggedMatch.tags))
        # Explicitly state the starting table
        .select_from(LoggedMatch)
        # --- UPDATED JOINS ---
        # Join Deck directly using LoggedMatch.deck_id
        .join(Deck, LoggedMatch.deck_id == Deck.id)
        # Join DeckType directly from Deck
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        # --- END UPDATED JOINS ---

        # --- CORE FILTERS ---
        # Filter by the user who logged the match
        .filter(LoggedMatch.logger_user_id == user_id) # Use logger_user_id
        # Filter out matches that have been soft-deleted
        .filter(LoggedMatch.is_active == True)
        # Filter out matches whose associated Deck has been soft-deleted
        .filter(Deck.is_active == True)
        # --- END CORE FILTERS ---
    )

    # --- OPTIONAL FILTERS ---
    # Apply deck filter if provided (filters by the deck used in the match)
    if deck_id is not None:
        query_builder = query_builder.filter(Deck.id == deck_id) # Filter on Deck.id

    # Apply tag filter if provided
    if tag_ids:
        query_builder = query_builder.filter(LoggedMatch.tags.any(Tag.id.in_(tag_ids)))

    # --- ORDERING ---
    # Order the results by timestamp, newest first
    query_builder = query_builder.order_by(desc(LoggedMatch.timestamp))

    # --- PAGINATION ---
    # Apply limit and offset if provided and valid
    if limit is not None and limit > 0:
        current_offset = offset if (offset is not None and offset >= 0) else 0
        query_builder = query_builder.limit(limit).offset(current_offset)

    # Execute the query and fetch all results
    results = query_builder.all()
    logger.debug(f"Found {len(results)} matches for user_id: {user_id}")

    # The results are already in the desired [(LoggedMatch, Deck, DeckType), ...] format
    return results