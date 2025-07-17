# backend/services/matches/match_history_service.py

from sqlalchemy.orm import selectinload
from backend import db
from backend.models import LoggedMatch, Deck, DeckType, Tag, OpponentCommanderInMatch, Commander, CommanderDeck
from sqlalchemy import desc
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

def get_matches_by_user(user_id, deck_id=None, limit=None, offset=None, tag_ids=None):
    """
    Fetches a list of matches for a user, including detailed opponent commander info
    and the user's own deck's commander info.
    """
    stmt = (
        db.session.query(LoggedMatch)
        .options(
            selectinload(LoggedMatch.tags),
            selectinload(LoggedMatch.opponent_commanders).selectinload(OpponentCommanderInMatch.commander),
            selectinload(LoggedMatch.deck).selectinload(Deck.deck_type),
            selectinload(LoggedMatch.deck)
                .selectinload(Deck.commander_decks)
                .options(
                    selectinload(CommanderDeck.commander),
                    selectinload(CommanderDeck.associated_commander)
                )
        )
        .filter(LoggedMatch.logger_user_id == user_id)
        .filter(LoggedMatch.is_active == True)
        .order_by(desc(LoggedMatch.timestamp))
    )

    if deck_id is not None:
        stmt = stmt.filter(LoggedMatch.deck_id == deck_id)

    if tag_ids:
        stmt = stmt.filter(LoggedMatch.tags.any(Tag.id.in_(tag_ids)))

    if limit is not None and limit > 0:
        current_offset = offset if (offset is not None and offset >= 0) else 0
        stmt = stmt.limit(limit).offset(current_offset)

    matches = stmt.all()

    results = []
    for match in matches:
        # --- Process Opponent Commanders ---
        opponents_by_seat = defaultdict(list)
        for opp_commander in sorted(match.opponent_commanders, key=lambda x: (x.seat_number, x.role)):
            commander_obj = opp_commander.commander
            if commander_obj:
                opponents_by_seat[opp_commander.seat_number].append({
                    "name": commander_obj.name,
                    "art_crop": commander_obj.art_crop
                })
        opponent_command_zones = list(opponents_by_seat.values())

        # --- Process User's Deck Commanders ---
        user_deck_command_zone = []
        # Check if the deck and its commander_decks object exist
        if match.deck and match.deck.commander_decks:
            # THE FIX IS HERE: Access the object directly, not as a list item
            commander_deck_entry = match.deck.commander_decks
            
            if commander_deck_entry.commander:
                user_deck_command_zone.append({
                    "name": commander_deck_entry.commander.name,
                    "art_crop": commander_deck_entry.commander.art_crop
                })
            if commander_deck_entry.associated_commander:
                user_deck_command_zone.append({
                    "name": commander_deck_entry.associated_commander.name,
                    "art_crop": commander_deck_entry.associated_commander.art_crop
                })
        
        results.append((
            match,
            match.deck,
            match.deck.deck_type if match.deck else None,
            user_deck_command_zone,
            opponent_command_zones
        ))

    return results