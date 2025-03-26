from backend import db
from backend.models.match import Match
from backend.models.user_deck import UserDeck
from backend.models.deck import Deck

from sqlalchemy import func, case

RESULT_WIN_ID = 0

def get_all_decks_stats(user_id):

    decks = (
    db.session.query(
        Deck.id,
        Deck.name,
        Deck.deck_type_id,
        func.count(Match.id).label("total_matches"),
        func.sum(case((Match.result == RESULT_WIN_ID, 1), else_=0)).label("total_wins"),
    )
    .join(UserDeck, UserDeck.deck_id == Deck.id)
    .outerjoin(Match, Match.user_deck_id == UserDeck.id)
    .filter(UserDeck.user_id == user_id) 
    .group_by(Deck.id) 
    .all()
)

    return [
        {
            "id": deck.id,
            "name": deck.name,
            "type": deck.deck_type_id,
            "total_matches": deck.total_matches,
            "total_wins": deck.total_wins,
            "win_rate": round((deck.total_wins / deck.total_matches) * 100, 2) if deck.total_matches > 0 else 0
        }
        for deck in decks
    ]

def get_deck_stats(user_id, deck_id):

    deck = (
    db.session.query(
        Deck.id,
        Deck.name,
        Deck.deck_type_id,
        func.count(Match.id).label("total_matches"),
        func.sum(case((Match.result == RESULT_WIN_ID, 1), else_=0)).label("total_wins"),
    )
    .join(UserDeck, UserDeck.deck_id == Deck.id)
    .outerjoin(Match, Match.user_deck_id == UserDeck.id)
    .filter(UserDeck.user_id == user_id, Deck.id == deck_id) 
    .group_by(Deck.id) 
    .first()
    )

    if deck is None:
        return None

    return {
            "id": deck.id,
            "name": deck.name,
            "total_matches": deck.total_matches,
            "total_wins": deck.total_wins,
            "win_rate": round((deck.total_wins / deck.total_matches) * 100, 2) if deck.total_matches > 0 else 0
        }
