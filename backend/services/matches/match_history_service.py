from backend import db
from backend.models.match import Match
from backend.models.deck import Deck
from backend.models.deck_type import DeckType
from backend.models.user_deck import UserDeck
from sqlalchemy import desc
import pprint

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

    printable_list = []
    if results:
        for match_obj, deck_obj, deck_type_obj in results:
            timestamp_str = match_obj.timestamp.strftime("%Y-%m-%d %H:%M:%S") if match_obj.timestamp else None
            printable_list.append({
                "match": {
                    "id": match_obj.id,
                    "result": match_obj.result,
                    "timestamp": timestamp_str
                },
                "deck": {
                    "id": deck_obj.id,
                    "name": deck_obj.name
                },
                "deck_type": {
                    "id": deck_type_obj.id,
                    "name": deck_type_obj.name
                }
                # Añade más campos si los necesitas
            })

    print("--- Match History Details (Pretty Print) ---")
    pprint.pprint(printable_list, indent=2, width=120) # Ajusta indent y width según necesites
    print("--------------------------------------------")

    return results