# backend/services/matches/match_history_service.py

from sqlalchemy.orm import selectinload
from backend import db
# Ensure all required models are imported
from backend.models import Match, Deck, DeckType, UserDeck, Tag
from sqlalchemy import desc
# No need to import true_ or false_ for basic boolean filtering

def get_matches_by_user(user_id, deck_id=None, limit=None, offset=None, tag_ids=None):
    """
    Fetches match history for a user, returning only matches that are active
    AND associated with an active deck.

    Args:
        user_id (int): The ID of the user whose matches to fetch.
        deck_id (int, optional): Filter matches by a specific deck ID. Defaults to None.
        limit (int, optional): Maximum number of matches to return. Defaults to None.
        offset (int, optional): Number of matches to skip. Defaults to None.
        tag_ids (list[int], optional): Filter matches by associated tag IDs. Defaults to None.

    Returns:
        List[Tuple[Match, Deck, DeckType]]: A list of tuples containing the
                                            Match, associated Deck, and DeckType objects.
    """

    # Start building the query, selecting the necessary objects
    query_builder = (
        db.session.query(
            Match,
            Deck,
            DeckType
        )
        # Eager load tags for each match to prevent N+1 queries later
        .options(selectinload(Match.tags))
        # Explicitly state the starting table (good practice, though often inferred)
        .select_from(Match)
        # Join through UserDeck to filter by user_id and link to Deck
        .join(UserDeck, Match.user_deck_id == UserDeck.id)
        # Join Deck to filter by deck_id (optional) and deck's active status
        .join(Deck, UserDeck.deck_id == Deck.id)
        # Join DeckType to retrieve its information
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        # --- CORE FILTERS ---
        # Filter by the requesting user
        .filter(UserDeck.user_id == user_id)
        # Filter out matches that have been soft-deleted using Python's True
        .filter(Match.is_active == True)
        # Filter out matches whose associated Deck has been soft-deleted using Python's True
        .filter(Deck.is_active == True)
        # --- END CORE FILTERS ---
    )

    # --- OPTIONAL FILTERS ---
    # Apply deck filter if provided
    if deck_id is not None:
        # This filter now implicitly only applies to *active* decks due to the core filter above
        query_builder = query_builder.filter(Deck.id == deck_id)

    # Apply tag filter if provided
    if tag_ids:
        # Filter matches that have *at least one* of the specified tags
        query_builder = query_builder.filter(Match.tags.any(Tag.id.in_(tag_ids)))
        # Note: .any() is generally efficient for checking existence in a relationship

    # --- ORDERING ---
    # Order the results by timestamp, newest first
    query_builder = query_builder.order_by(desc(Match.timestamp))

    # --- PAGINATION ---
    # Apply limit and offset if provided and valid
    if limit is not None and limit > 0:
        # Ensure offset is non-negative, default to 0 if None or negative
        current_offset = offset if (offset is not None and offset >= 0) else 0
        query_builder = query_builder.limit(limit).offset(current_offset)

    # Execute the query and fetch all results
    results = query_builder.all()

    # The results are already in the desired [(Match, Deck, DeckType), ...] format
    return results