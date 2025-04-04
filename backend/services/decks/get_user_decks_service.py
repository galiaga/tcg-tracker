from backend import db
from backend.models import Deck, DeckType, Tag
from sqlalchemy.orm import selectinload

def get_user_decks(user_id, deck_type_id=None, tag_ids=None):
    query = (
        db.session.query(Deck, DeckType)
        .options(selectinload(Deck.tags))
        .join(DeckType, Deck.deck_type_id == DeckType.id)
        .filter(Deck.user_id == user_id)
    )

    apply_deck_type_filter = False
    valid_deck_type_id = None
    if deck_type_id is not None:
        deck_type_id_str = str(deck_type_id).lower().strip()
        if deck_type_id_str not in ['', 'all', '0']:
            try:
                valid_deck_type_id = int(deck_type_id_str)
                apply_deck_type_filter = True
            except (ValueError, TypeError):
                apply_deck_type_filter = False

    if apply_deck_type_filter:
        query = query.filter(Deck.deck_type_id == valid_deck_type_id)

    if tag_ids:
        query = query.filter(Deck.tags.any(Tag.id.in_(tag_ids)))

    query = query.order_by(Deck.name.asc())

    return query.all()