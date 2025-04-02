from backend.models.match import Match
from backend.models.deck import Deck
from backend.models.deck_type import DeckType
from backend import db

def get_all_matches():
    return Match.query.order_by(Match.date.desc()).all()

def get_matches_by_user(user_id, deck_id=None, limit=None, offset=None):
    if deck_id:
        query_builder = (
            db.session.query(Match, Deck, DeckType)
            .join(Deck, Match.user_deck_id == Deck.id)
            .join(DeckType, Deck.deck_type_id == DeckType.id)
            .filter(Deck.user_id == user_id, Deck.id == deck_id)
            .order_by(Match.timestamp.desc())
        )
    else:
        query_builder = (
            db.session.query(Match, Deck, DeckType)
                .join(Deck, Match.user_deck_id == Deck.id)
                .join(DeckType, Deck.deck_type_id == DeckType.id)
                .filter(Deck.user_id == user_id)
                .order_by(Match.timestamp.desc())
        )

    if limit is not None and limit > 0:
        current_offset = offset if (offset is not None and offset >= 0) else 0
        query_builder = query_builder.offset(current_offset).limit(limit)

    results = query_builder.all()
    return results