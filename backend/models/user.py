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
    username = db.Column(String(80), unique=True, nullable=False)
    email = db.Column(String(120), unique=True, nullable=True, index=True) # Nullable initially for existing users
    password_hash = db.Column(String(255), nullable=False) # Stores hash from Flask-Bcrypt

    # --- Soft Delete Implementation ---
    is_active = db.Column(Boolean, nullable=False, default=True, server_default=text('TRUE'), index=True)
    deleted_at = db.Column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    # Example: One-to-Many relationship with Tag model
    tags = db.relationship("Tag", back_populates="user", cascade="all, delete-orphan")

    # --- Instance Methods ---
    def soft_delete(self):
        """Marks the user as inactive and records the deletion timestamp."""
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)
        db.session.add(self) # Ensure changes are staged for commit

    def __repr__(self):
        """Provides a developer-friendly string representation of the user."""
        active_status = "Active" if self.is_active else "Deleted"
        return f"<User id={self.id} username={self.username} email={self.email} status={active_status}>"

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
        return cls.query_active().filter(func.lower(cls.email) == func.lower(email)).first()

    @classmethod
    def find_by_username(cls, username):
        """Finds an active user by username."""
        if not username:
            return None
        return cls.query_active().filter(cls.username == username).first()