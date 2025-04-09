from backend import create_app, db
from scripts.seed_data.deck_types import seed_deck_types
from scripts.seed_data.commanders import seed_commanders

app = create_app()

with app.app_context():
    seed_deck_types(db)
    seed_commanders(db)
    print("🎉 Seeding completo.")
