from backend import db
from backend.models.match import Match
from backend.models.user_deck import UserDeck
from backend.models.deck import Deck
from sqlalchemy import func, case, Integer

RESULT_WIN_ID = 0

_match_count_case = case((Match.id != None, 1), else_=0)
_win_count_case = case((Match.result == RESULT_WIN_ID, 1), else_=0)

def get_all_decks_stats(user_id):
    decks_stats = (
        db.session.query(
            Deck.id,
            Deck.name,
            Deck.deck_type_id,
            func.sum(_match_count_case).label("total_matches"),
            func.sum(_win_count_case).label("total_wins"),
            func.max(Match.timestamp).label("last_match")
        )
        .select_from(UserDeck)
        .join(Deck, UserDeck.deck_id == Deck.id)
        .outerjoin(Match, Match.user_deck_id == UserDeck.id)
        .filter(UserDeck.user_id == user_id)
        .group_by(Deck.id, Deck.name, Deck.deck_type_id)
        .order_by(Deck.name) 
        .all()
    )

    results = []
    for deck in decks_stats:
        total_matches = int(deck.total_matches or 0)
        total_wins = int(deck.total_wins or 0)
        win_rate = round((total_wins / total_matches) * 100, 2) if total_matches > 0 else 0

        results.append({
            "id": deck.id,
            "name": deck.name,
            "type": deck.deck_type_id,
            "total_matches": total_matches,
            "total_wins": total_wins,
            "win_rate": win_rate,
            "last_match": deck.last_match
        })
    return results

def get_deck_stats(user_id, deck_id):
    deck_stats = (
        db.session.query(
            Deck.id,
            Deck.name,
            func.sum(_match_count_case).cast(Integer).label("total_matches"),
            func.sum(_win_count_case).cast(Integer).label("total_wins"),
        )
        .select_from(UserDeck)
        .join(Deck, UserDeck.deck_id == Deck.id)
        .outerjoin(Match, Match.user_deck_id == UserDeck.id)
        .filter(UserDeck.user_id == user_id, Deck.id == deck_id)
        .group_by(Deck.id, Deck.name)
        .first()
    )

    if deck_stats is None:
        return None

    total_matches = int(deck_stats.total_matches or 0)
    total_wins = int(deck_stats.total_wins or 0)
    win_rate = round((total_wins / total_matches) * 100, 2) if total_matches > 0 else 0

    return {
            "id": deck_stats.id,
            "name": deck_stats.name,
            "total_matches": total_matches,
            "total_wins": total_wins,
            "win_rate": win_rate,
        }