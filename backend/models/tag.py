# backend/models/tag.py

from backend.database import db
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint, Boolean, DateTime, Index
from datetime import datetime, timezone
from .logged_match import match_tags

# --- Association Tables (No changes needed here) ---
deck_tags = db.Table('deck_tags',
    db.Column('deck_id', db.Integer, db.ForeignKey('decks.id', ondelete='CASCADE'), primary_key=True), # Consider CASCADE if Tag is hard-deleted
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)  # Consider CASCADE if Tag is hard-deleted
)

# NOTE: ON DELETE CASCADE on association tables is good practice even with soft delete on the Tag model,
# in case you ever *do* decide to hard delete a Tag later (e.g., for GDPR compliance or cleanup).
# It ensures the links are removed if the Tag row disappears.

class Tag(db.Model):
    __tablename__ = "tags"

    # --- Core Columns ---
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now()) # Explicit type

    # --- Soft Delete Columns ---
    is_active = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text('TRUE'), # Use text('TRUE') for DB compatibility
        index=True                   # Index for filtering active tags
    )
    deleted_at = db.Column(
        DateTime(timezone=True),
        nullable=True
    )

    # --- Relationships ---
    user = db.relationship("User", back_populates="tags")
    # These relationships don't strictly need changes for soft delete,
    # but filtering might happen when querying THROUGH them.
    decks = db.relationship(
        "Deck",
        secondary=deck_tags,
        back_populates="tags"
    )
    logged_matches = relationship(
        "LoggedMatch", # Use the new class name
        secondary=match_tags, # Use the imported table definition
        back_populates="tags" # Point back to the 'tags' attribute in LoggedMatch
    )

    # --- Table Arguments ---
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_tag_name'),
        # Optional: Index for querying active tags for a user
        # Index('ix_tags_user_id_is_active', 'user_id', 'is_active'),
    )

    # --- Instance Methods ---
    def soft_delete(self):
        """Marks the tag as inactive and records the deletion time."""
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        db.session.add(self) # Ensure object is in session

    def __repr__(self):
        active_status = "Active" if self.is_active else "Deleted"
        return f"<Tag id={self.id} user_id={self.user_id} name='{self.name}' status={active_status}>"

    # --- Class Methods (Optional Helpers) ---
    @classmethod
    def query_active(cls):
        """Returns a query object filtered by active tags."""
        # Remember to filter by user_id as well in actual usage
        return cls.query.filter(cls.is_active == True)