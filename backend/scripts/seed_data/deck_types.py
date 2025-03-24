# backend/scripts/seed_data/deck_types.py
from backend.models import DeckType

def seed_deck_types(db):
    if DeckType.query.first():
        print("🔸 Deck types ya están insertados.")
        return

    names = [
        "Standard",
        "Pioneer",
        "Modern",
        "Legacy",
        "Vintage",
        "Pauper",
        "Commander / EDH"
    ]

    db.session.add_all([DeckType(name=name) for name in names])
    db.session.commit()
    print("✅ Deck types insertados.")
