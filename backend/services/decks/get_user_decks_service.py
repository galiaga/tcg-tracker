from backend import db
from backend.models.deck import Deck
from backend.models.deck_type import DeckType

def get_user_decks(user_id):
    return (
        db.session.query(Deck, DeckType)
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        .filter(Deck.user_id == user_id)
        .order_by(Deck.name.desc())
        .all()
    )