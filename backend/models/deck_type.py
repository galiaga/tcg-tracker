from backend.database import db
from sqlalchemy import CheckConstraint


class DeckType(db.Model):
    __tablename__ = "deck_types"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    decks = db.relationship("Deck", back_populates="deck_type")