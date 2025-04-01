from backend import db
from backend.models.deck import Deck
from backend.models.deck_type import DeckType

def get_user_decks(user_id, deck_type_id=None):
    query = (
        db.session.query(Deck, DeckType)
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        .filter(Deck.user_id == user_id)
    )

    apply_filter = False
    if deck_type_id is not None and str(deck_type_id).lower not in ['', 'all', '0']:
        try:
            valid_deck_type_id = int(deck_type_id)
            apply_filter = True
        except (ValueError, TypeError):
            apply_filter = False
    
    if apply_filter:
        query = query.filter(Deck.deck_type_id == valid_deck_type_id)

    query = query.order_by(Deck.name.desc())

    return query.all()