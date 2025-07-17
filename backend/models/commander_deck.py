# backend/models/commander_deck.py

from backend.database import db
from sqlalchemy.orm import relationship

class CommanderDeck(db.Model):
    __tablename__ = 'commander_decks'

    id = db.Column(db.Integer, primary_key=True)
    # Make deck_id unique since a deck should only have one command zone entry.
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False, unique=True) 
    commander_id = db.Column(db.Integer, db.ForeignKey('commanders.id'), nullable=False)
    associated_commander_id = db.Column(db.Integer, db.ForeignKey('commanders.id'), nullable=True)

    # Relationship to the Deck
    deck = relationship("Deck", back_populates="commander_decks")

    # Relationship to the primary Commander
    commander = relationship(
        "Commander", 
        foreign_keys=[commander_id],
        backref=db.backref("primary_in_decks", lazy="dynamic") 
    )
    # Relationship to the associated Commander (if any)
    associated_commander = relationship(
        "Commander", 
        foreign_keys=[associated_commander_id],
        backref=db.backref("associated_in_decks", lazy="dynamic")
    )

    def __repr__(self):
        return f"<CommanderDeck DeckID:{self.deck_id} CmdrID:{self.commander_id} AssocID:{self.associated_commander_id}>"