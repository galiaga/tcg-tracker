from backend import db
from backend.models.deck_type import DeckType
from backend.models.commander_deck import CommanderDeck 
from sqlalchemy.sql import func


class Deck(db.Model):
    __tablename__ = "decks"

    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    deck_type_id = db.Column(db.Integer, db.ForeignKey('deck_types.id'), nullable=False)
    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now()
    )

    deck_type = db.relationship("DeckType", back_populates="decks")
    commander_decks = db.relationship("CommanderDeck", back_populates="deck", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "deck_type": {
                "id": self.deck_type.id,
                "name": self.deck_type.name
            },
            "win_rate": getattr(self, "win_rate", 0),
            "total_matches": getattr(self, "total_matches", 0),
            "total_wins": getattr(self, "total_wins", 0)
        }

        if self.deck_type_id == 7 and self.commander_decks:
            data["commander"] = {
                "commander_id": self.commander_decks.commander_id,
                "associated_commander_id": self.commander_decks.associated_commander_id
            }

        return data