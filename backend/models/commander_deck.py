from backend import db

class CommanderDeck(db.Model):
    __tablename__ = "commander_decks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("decks.id"), nullable=False)
    commander_id = db.Column(db.Integer, db.ForeignKey("commanders.id"), nullable=False)

    deck = db.relationship("Deck", back_populates="commander_decks")
    commander = db.relationship("Commander", back_populates="commander_decks")

    def __repr__(self):
        return f"<CommanderDeck deck_id={self.deck_id} commander_id={self.commander_id}>"
