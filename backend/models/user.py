# backend/models/user.py

from backend import db
# Import necessary types/functions
from sqlalchemy import Boolean, DateTime, Index, String, Integer # Explicit types
from sqlalchemy.sql import func, text # text for server_default
from datetime import datetime, timezone
# Import Tag for relationship definition (already present)
from backend.models.tag import Tag

class User(db.Model):
    __tablename__ = "users"

    # --- Core Columns ---
    id = db.Column(Integer, primary_key=True, autoincrement=True) # Explicit type
    username = db.Column(String(80), unique=True, nullable=False) # Explicit type
    hash = db.Column(String(255), nullable=False) # Explicit type

    # --- Soft Delete Columns ---
    is_active = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text('TRUE'), # Use text('TRUE') for DB compatibility
        index=True                   # Index for filtering active users (e.g., at login)
    )
    deleted_at = db.Column(
        DateTime(timezone=True),
        nullable=True
    )

    # --- Relationships ---
    # cascade="all, delete-orphan" means tags are deleted if the User is hard-deleted,
    # or if a tag is removed from the user.tags collection. This is usually fine
    # even with soft-delete on User, as soft-delete won't trigger the cascade.
    tags = db.relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    # Add other relationships if needed (e.g., back_populates for UserDeck)
    # user_decks = db.relationship("UserDeck", back_populates="user", cascade="all, delete-orphan") # Example

    # --- Instance Methods ---
    def soft_delete(self):
        """Marks the user as inactive and records the deletion time."""
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        # Consider other actions: anonymize data, clear session, etc.
        db.session.add(self) # Ensure object is in session

    def __repr__(self):
        active_status = "Active" if self.is_active else "Deleted"
        return f"<User id={self.id} username={self.username} status={active_status}>"

    # --- Class Methods (Optional Helpers) ---
    @classmethod
    def query_active(cls):
        """Returns a query object filtered by active users."""
        return cls.query.filter(cls.is_active == True)