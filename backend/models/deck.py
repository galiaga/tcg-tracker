# backend/models/deck.py

from backend import db
# Keep your existing imports: DeckType, CommanderDeck, deck_tags
from backend.models.deck_type import DeckType
from backend.models.commander_deck import CommanderDeck
from backend.models.tag import deck_tags
from sqlalchemy.sql import func
from datetime import datetime, timezone # Import datetime and timezone

class Deck(db.Model):
    __tablename__ = "decks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    deck_type_id = db.Column(db.Integer, db.ForeignKey('deck_types.id'), nullable=False)
    creation_date = db.Column(
        db.DateTime(timezone=True), # Good practice to use timezone=True
        nullable=False,
        server_default=func.now() # func.now() usually respects DB timezone settings
    )

    # --- NEW COLUMNS for Soft Delete ---
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,  # New decks are active by default
        index=True     # Add an index for faster querying on active decks
    )
    deleted_at = db.Column(
        db.DateTime(timezone=True), # Store deletion time with timezone
        nullable=True               # Null if the deck is active
    )
    # --- End of New Columns ---

    # --- Relationships (No changes needed here for soft delete itself) ---
    tags = db.relationship(
        "Tag",
        secondary=deck_tags,
        back_populates="decks"
        # Consider if you need to filter tags based on active decks later
    )

    deck_type = db.relationship("DeckType", back_populates="decks")
    # cascade="all, delete-orphan" on commander_decks:
    # delete-orphan still makes sense if you disassociate a commander from a deck.
    # The 'delete' part of the cascade won't trigger on soft delete, which is fine.
    commander_decks = db.relationship("CommanderDeck", back_populates="deck", uselist=False, cascade="all, delete-orphan")

    # --- Methods (No changes needed in to_dict for now) ---
    def to_dict(self):
        # This method doesn't need changes now, but the code CALLING it
        # should ensure it only gets called for active decks.
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

    # --- Optional: Add a helper method for soft deleting ---
    def soft_delete(self):
        """Marks the deck as inactive and records the deletion time."""
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc) # Use UTC for consistency
        db.session.add(self) # Ensure the object is added to the session if detached

# --- Optional: Add a helper method for querying active decks ---
# This can help prevent forgetting the filter later
@classmethod
def query_active(cls):
    """Returns a query object filtered by active decks."""
    return cls.query.filter(cls.is_active == True)

# Add the class method to the Deck class if you like this approach
# Deck.query_active = query_active # Uncomment this line if you add the method outside the class
# Or just define it inside the class like soft_delete above