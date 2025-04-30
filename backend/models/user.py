# backend/models/user.py

# --- Necessary Imports ---
from backend import db
from sqlalchemy import Boolean, DateTime, Index, String, Integer
from sqlalchemy.sql import func, text
from datetime import datetime, timezone
from backend.models.tag import Tag # Example relationship import

# --- User Model Definition ---
class User(db.Model):
    __tablename__ = "users"

    # --- Core User Attributes ---
    id = db.Column(Integer, primary_key=True, autoincrement=True)

    # NEW: First and Last Name (Required)
    first_name = db.Column(String(100), nullable=False)
    last_name = db.Column(String(100), nullable=False)

    # UPDATED: Email (Now Required & Unique)
    # Essential for communication, password recovery, and potentially login.
    email = db.Column(String(120), unique=True, nullable=False, index=True)

    # UPDATED: Username (Now Optional, but still Unique if provided)
    # IMPORTANT: If your login system currently REQUIRES username, keep nullable=False
    # until you have updated your authentication logic to use email instead.
    # If kept, ensure it remains unique if a value is provided.
    username = db.Column(String(80), unique=True, nullable=True) # Changed nullable to True

    password_hash = db.Column(String(255), nullable=False) # Stores hash from Flask-Bcrypt

    # --- Soft Delete Implementation ---
    is_active = db.Column(Boolean, nullable=False, default=True, server_default=text('TRUE'), index=True)
    deleted_at = db.Column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    # Example: One-to-Many relationship with Tag model
    tags = db.relationship("Tag", back_populates="user", cascade="all, delete-orphan")

    # --- Properties ---
    @property
    def full_name(self):
        """Returns the user's full name."""
        # Handles potential edge cases, though first/last name are required
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    # --- Instance Methods ---
    def soft_delete(self):
        """Marks the user as inactive and records the deletion timestamp."""
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        db.session.add(self) # Ensure changes are staged for commit

    def __repr__(self):
        """Provides a developer-friendly string representation of the user."""
        active_status = "Active" if self.is_active else "Deleted"
        # Updated representation to include full name
        return f"<User id={self.id} name='{self.full_name}' email={self.email} username={self.username} status={active_status}>"

    # --- Class Methods (Query Helpers) ---
    @classmethod
    def query_active(cls):
        """Base query to filter only active users."""
        return cls.query.filter(cls.is_active == True)

    @classmethod
    def find_by_email(cls, email):
        """Finds an active user by email (case-insensitive)."""
        if not email:
            return None
        # Ensure email comparison is case-insensitive
        return cls.query_active().filter(func.lower(cls.email) == func.lower(email)).first()

    @classmethod
    def find_by_username(cls, username):
        """Finds an active user by username (if username is provided)."""
        if not username: # If username is optional, searching for None/empty is pointless
            return None
        return cls.query_active().filter(cls.username == username).first()

    # Consider adding other finders if needed, e.g., find_by_id
    @classmethod
    def find_by_id(cls, user_id):
        """Finds an active user by their primary key ID."""
        if not user_id:
            return None
        return cls.query_active().filter(cls.id == user_id).first()