import os
from datetime import timedelta
from flask import jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from backend import create_app, db
from backend.models import DeckType

app = create_app()

bcrypt = Bcrypt(app)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
jwt = JWTManager(app)

migrate = Migrate(app, db)

RESULT_MAPPING = {0: "Lose", 1: "Win", 2: "Draw"}

DECK_TYPE_NAMES = [
    "Standard",
    "Pioneer",
    "Modern",
    "Legacy",
    "Vintage",
    "Pauper",
    "Commander / EDH"
]

@app.cli.command("seed-deck-types")
def seed_deck_types():
    print("Seeding deck types...")
    count = 0
    try:
        for name in DECK_TYPE_NAMES:
            existing_type = db.session.execute(
                db.select(DeckType).filter_by(name=name)
            ).scalar_one_or_none()

            if not existing_type:
                new_deck_type = DeckType(name=name)
                db.session.add(new_deck_type)
                print(f"  + Adding DeckType: {name}")
                count += 1
            else:
                print(f"  = DeckType '{name}' already exists, skipping.")

        if count > 0:
            db.session.commit()
            print(f"Successfully added {count} new deck types.")
        else:
            print("No new deck types to add.")
        print("Deck type seeding finished.")
    except Exception as e:
        db.session.rollback()
        print(f"ERROR seeding deck types: {e}")

@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"error": "Missing or invalid token"}), 401

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the API"}), 200

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)