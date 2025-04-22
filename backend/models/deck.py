# backend/models/deck.py

from backend import db
from backend.models.deck_type import DeckType
from backend.models.commander_deck import CommanderDeck
from backend.models.tag import deck_tags
from sqlalchemy.sql import func, text # Import text for server_default
from sqlalchemy import Boolean, DateTime, Index # Import Boolean, DateTime, Index
from datetime import datetime, timezone

# --- Deck Model ---
class Deck(db.Model):
    __tablename__ = "decks"

    # --- Columns ---
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    deck_type_id = db.Column(db.Integer, db.ForeignKey('deck_types.id'), nullable=False)
    creation_date = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # --- Soft Delete Columns ---
    is_active = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text('TRUE'), # Use text for DB compatibility
        index=True
    )
    deleted_at = db.Column(
        DateTime(timezone=True),
        nullable=True
    )

    # --- Relationships ---
    tags = db.relationship(
        "Tag",
        secondary=deck_tags,
        back_populates="decks"
    )
    deck_type = db.relationship("DeckType", back_populates="decks")
    commander_decks = db.relationship("CommanderDeck", back_populates="deck", uselist=False, cascade="all, delete-orphan")

    # --- Instance Methods ---
    def to_dict(self):
        # Note: Callers should ensure this is only used for active decks
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
        if self.deck_type_id == 7 and self.commander_decks: # Assuming 7 is Commander format ID
            data["commander"] = {
                "commander_id": self.commander_decks.commander_id,
                "associated_commander_id": self.commander_decks.associated_commander_id
            }
        return data

    def soft_delete(self):
        """Marks the deck as inactive and records the deletion time."""
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        db.session.add(self)

    # --- Class Methods ---
    @classmethod
    def query_active(cls):
        """Returns a query object filtered by active decks."""
        return cls.query.filter(cls.is_active == True)