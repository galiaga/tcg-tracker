from backend import db
from sqlalchemy.orm import make_transient

class CommanderDeck(db.Model):
    __tablename__ = "commander_decks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("decks.id"), nullable=False)
    commander_id = db.Column(db.Integer, db.ForeignKey("commanders.id"), nullable=False)
    associated_commander_id = db.Column(db.Integer, nullable=True)
    relationship_type = db.Column(db.String, nullable=True)

    deck = db.relationship("Deck", back_populates="commander_decks")
    commander = db.relationship("Commander", foreign_keys=[commander_id], back_populates="commander_decks")

    def get_associated_commander(self):
        if not self.associated_commander_id:
            return None

        commander_table = db.Model.metadata.tables["commanders"]
        result = db.session.execute(
            db.select(commander_table).where(commander_table.c.id == self.associated_commander_id)
        ).fetchone()

        if result:
            from backend.models import Commander
            commander_obj = Commander(**dict(result._mapping))
            make_transient(commander_obj)
            return commander_obj

        return None

    def __repr__(self):
        return f"<CommanderDeck deck_id={self.deck_id} commander_id={self.commander_id}>"
