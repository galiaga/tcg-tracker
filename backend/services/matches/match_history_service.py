from backend import db
from backend.models.match import Match
from backend.models.deck import Deck
from backend.models.deck_type import DeckType
from backend.models.user_deck import UserDeck
from sqlalchemy import desc

def get_matches_by_user(user_id, deck_id=None, limit=None, offset=None):

    query_builder = (
        db.session.query(
            Match,
            Deck,
            DeckType
        )
        .select_from(Match) 
        .join(UserDeck, Match.user_deck_id == UserDeck.id) 
        .join(Deck, UserDeck.deck_id == Deck.id)          
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        .filter(UserDeck.user_id == user_id)      
    )

    if deck_id is not None:
        query_builder = query_builder.filter(Deck.id == deck_id)

    query_builder = query_builder.order_by(desc(Match.timestamp))

    if limit is not None and limit > 0:
        current_offset = offset if (offset is not None and offset >= 0) else 0
        query_builder = query_builder.limit(limit).offset(current_offset)

    results = query_builder.all()
    return results