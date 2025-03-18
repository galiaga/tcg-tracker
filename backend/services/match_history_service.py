from backend.models.match import Match
from backend.models.deck import Deck
from backend.models.deck_type import DeckType
from backend import db

# Get all matches
def get_all_matches():
    return Match.query.order_by(Match.date.desc()).all()

# # Get user's matches
def get_matches_by_user(user_id):
    return (
        db.session.query(Match, Deck, DeckType)
        .join(Deck, Match.user_deck_id == Deck.id)
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        .filter(Deck.user_id == user_id)
        .order_by(Match.timestamp.desc())
        .all()
    )
