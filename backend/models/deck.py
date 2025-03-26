from backend import db
from backend.models.deck_type import DeckType
from backend.models.commander_deck import CommanderDeck 

class Deck(db.Model):
    __tablename__ = "decks"

    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    deck_type_id = db.Column(db.Integer, db.ForeignKey('deck_types.id'), nullable=False)

    deck_type = db.relationship("DeckType", back_populates="decks")
    commander_decks = db.relationship("CommanderDeck", back_populates="deck", cascade="all, delete-orphan") 

    def to_dict(self):
        return {
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