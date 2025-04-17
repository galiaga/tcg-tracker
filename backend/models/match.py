# backend/models/match.py

from backend import db
from sqlalchemy.sql import func, text # Import text for server_default
from sqlalchemy import CheckConstraint, Boolean, DateTime, Index # Import Boolean, DateTime, Index
from backend.models.tag import match_tags
from datetime import datetime, timezone

class Match(db.Model):
    __tablename__ = "matches"

    # --- Core Columns ---
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(
        DateTime(timezone=True), # Explicit type
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    result = db.Column(db.Integer, nullable=False)  # 0 = Lose, 1 = Win, 2 = Draw
    user_deck_id = db.Column(db.Integer, db.ForeignKey("user_decks.id"), nullable=False)

    # --- Soft Delete Columns ---
    is_active = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text('TRUE'), # Use text('TRUE') for DB compatibility
        index=True                   # Index for filtering active matches
    )
    deleted_at = db.Column(
        DateTime(timezone=True),
        nullable=True
    )

    # --- Relationships ---
    user_deck = db.relationship("UserDeck", back_populates="matches")
    tags = db.relationship(
        "Tag",
        secondary=match_tags,
        back_populates="matches",
        # Consider if you need lazy='dynamic' or filtering here later
    )

    # --- Table Arguments ---
    __table_args__ = (
        CheckConstraint("result IN (0, 1, 2)", name="check_match_result"),
        # Optional: Add index for common queries involving user_deck_id and is_active
        # Index('ix_matches_user_deck_id_is_active', 'user_deck_id', 'is_active'),
    )

    # --- Instance Methods ---
    def soft_delete(self):
        """Marks the match as inactive and records the deletion time."""
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        db.session.add(self) # Ensure object is in session

    def __repr__(self):
        active_status = "Active" if self.is_active else "Deleted"
        return f"<Match id={self.id} result={self.result} timestamp={self.timestamp} status={active_status}>"

    # --- Class Methods (Optional Helpers) ---
    @classmethod
    def query_active(cls):
        """Returns a query object filtered by active matches."""
        return cls.query.filter(cls.is_active == True)