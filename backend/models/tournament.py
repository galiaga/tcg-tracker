# backend/models/tournament.py

from datetime import datetime
from sqlalchemy.dialects.postgresql import ENUM as PgEnum # If using Enums later
from sqlalchemy import UniqueConstraint, Index
from backend import db
# Assuming you have base model mixins like this:
# from .base import BaseModel, TimestampMixin, SoftDeleteMixin
# If not, you'll need to add the columns/methods directly or create the mixins.

# Let's assume SoftDeleteMixin provides is_active, deleted_at, soft_delete(), query_active()
# and TimestampMixin provides created_at, updated_at (though updated_at isn't strictly needed here yet)
# If these mixins don't exist, add the columns manually as shown below.

class Tournament(db.Model):
    """Represents a tournament event."""
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    format = db.Column(db.String(50), nullable=True) # e.g., 'Commander', 'Modern', 'Sealed'
    status = db.Column(db.String(20), nullable=False, default='Planned', index=True) # Planned, Active, Completed, Cancelled
    pairing_system = db.Column(db.String(30), nullable=False, default='Swiss') # e.g., 'Swiss', 'Round Robin', 'Single Elimination'
    max_players = db.Column(db.Integer, nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Standard Columns (assuming no mixins for now, add them explicitly)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    # updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now(), nullable=False) # Good practice, but not requested
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True) # For soft delete
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True) # For soft delete timestamp

    # Relationships
    organizer = db.relationship("User", backref=db.backref("organized_tournaments", lazy="dynamic"))

    # Use back_populates for clear bidirectional linking
    participants = db.relationship(
        "TournamentParticipant",
        back_populates="tournament",
        lazy="dynamic",
        cascade="all, delete-orphan" # If a tournament is hard-deleted, delete participants
    )

    # Placeholder for future EventMatch relationship
    # event_matches = db.relationship("EventMatch", back_populates="tournament", lazy="dynamic")

    # --- Soft Delete Methods (Implement or use Mixin) ---
    def soft_delete(self):
        """Marks the record as inactive and sets the deleted_at timestamp."""
        self.is_active = False
        self.deleted_at = datetime.utcnow() # Or use db.func.now() if appropriate for DB timezone handling
        db.session.add(self)

    @classmethod
    def query_active(cls):
        """Returns a query object filtered by active records."""
        return cls.query.filter_by(is_active=True)
    # --- End Soft Delete Methods ---

    def __repr__(self):
        return f'<Tournament {self.id}: {self.name} ({self.status})>'


class TournamentParticipant(db.Model):
    """Represents a user's participation in a specific tournament with a specific deck."""
    __tablename__ = 'tournament_participants'
    # Ensure unique constraint name is <= 63 chars for PostgreSQL
    __table_args__ = (
        UniqueConstraint('tournament_id', 'user_id', name='uq_tournament_user'),
        # Add indexes explicitly if needed, though FKs often get them implicitly
        # Index('ix_tournament_participants_tournament_id', 'tournament_id'),
        # Index('ix_tournament_participants_user_id', 'user_id'),
        # Index('ix_tournament_participants_deck_id', 'deck_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Assuming a participant MUST register with a deck. Make nullable=True if optional.
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    registration_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    dropped = db.Column(db.Boolean, default=False, nullable=False, index=True) # Indexed for finding active players

    # Standard Columns (assuming no mixins for now, add them explicitly)
    # created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False) # Redundant with registration_date? Maybe keep for consistency.
    # updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now(), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True) # For soft delete
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True) # For soft delete timestamp

    # Relationships
    tournament = db.relationship("Tournament", back_populates="participants")
    user = db.relationship("User", backref=db.backref("tournament_participations", lazy="dynamic"))
    # Use 'select' loading (default) for deck, as we usually need the specific deck info when accessing participant
    deck = db.relationship("Deck", backref=db.backref("tournament_registrations", lazy="select"))

    # Placeholder for future EventMatchEntry relationship
    # event_match_entries = db.relationship("EventMatchEntry", back_populates="participant", lazy="dynamic")

    # --- Soft Delete Methods (Implement or use Mixin) ---
    def soft_delete(self):
        """Marks the record as inactive and sets the deleted_at timestamp."""
        self.is_active = False
        self.deleted_at = datetime.utcnow() # Or use db.func.now()
        db.session.add(self)

    @classmethod
    def query_active(cls):
        """Returns a query object filtered by active records."""
        return cls.query.filter_by(is_active=True)
    # --- End Soft Delete Methods ---


    def __repr__(self):
        status = "Dropped" if self.dropped else "Active"
        return f'<TournamentParticipant {self.id}: User {self.user_id} in Tourn {self.tournament_id} ({status})>'