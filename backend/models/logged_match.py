# backend/models/logged_match.py
import enum
from sqlalchemy import UniqueConstraint, Index, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship # Ensure relationship is imported
from backend.database import db
# Assuming SoftDeleteMixin and TimestampMixin exist and provide relevant columns/methods
# from .base import SoftDeleteMixin, TimestampMixin

# Define Enum for results
class LoggedMatchResult(enum.Enum):
    WIN = 0
    LOSS = 1
    DRAW = 2

# Define the association table for tags (keep the name for now)
# Alembic *should* detect the FK rename later, but we verify.
match_tags = db.Table('match_tags',
    db.Column('match_id', db.Integer, db.ForeignKey('logged_matches.id', ondelete='CASCADE'), primary_key=True), # Keep 'matches.id' temporarily for Alembic detection
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

# Rename class, keep __tablename__ temporarily for Alembic
class LoggedMatch(db.Model):
    # Keep original table name for Alembic to detect rename operation
    __tablename__ = 'logged_matches'

    # Keep existing columns (adjust if using mixins)
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True) # Add index if not present
    result = db.Column(db.Integer, nullable=False) # Keep as Integer for DB

    # --- Soft Delete Columns (assuming no mixin) ---
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # --- End Soft Delete Columns ---

    # --- Add New Columns ---
    # These will be added by Alembic, initially nullable for data migration
    logger_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True) # Start nullable, add index
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=True, index=True) # Start nullable, add index
    opponent_description = db.Column(db.Text, nullable=True) # Optional text field for opponents
    match_format = db.Column(db.String(50), nullable=True) # Optional format (e.g., 'Commander', 'Casual')

    # --- Remove Old Column Definition ---
    # The user_deck_id column definition is removed from the model.
    # Alembic will detect this and generate a drop column operation.
    # user_deck_id = db.Column(db.Integer, db.ForeignKey('user_decks.id'), nullable=False) # REMOVE THIS LINE

    # --- Define New Relationships ---
    logger = relationship("User", backref=db.backref("logged_matches", lazy="dynamic"))
    deck = relationship("Deck", backref=db.backref("logged_matches", lazy="dynamic"))

    # Update relationship to Tag using the renamed class and updated secondary table
    tags = relationship("Tag", secondary=match_tags, back_populates="logged_matches") # Update back_populates target

    # --- Remove Old Relationship ---
    # user_deck = relationship("UserDeck", backref=db.backref("matches", lazy="dynamic")) # REMOVE THIS LINE

    # --- Constraints ---
    __table_args__ = (
        CheckConstraint('result IN (0, 1, 2)', name='check_logged_match_result'), # Rename constraint if desired
        # Add other constraints or indexes if needed
        # Index('ix_logged_matches_timestamp', 'timestamp'), # Example if not added above
    )

    # --- Enum Helper ---
    def get_result_enum(self) -> LoggedMatchResult | None:
        """Returns the result as a LoggedMatchResult enum member."""
        try:
            return LoggedMatchResult(self.result)
        except ValueError:
            return None # Or raise an error

    # --- Soft Delete Methods (Implement or use Mixin) ---
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = db.func.now() # Use DB function for consistency
        db.session.add(self)

    @classmethod
    def query_active(cls):
        return cls.query.filter_by(is_active=True)
    # --- End Soft Delete Methods ---

    def __repr__(self):
        result_str = self.get_result_enum().name if self.get_result_enum() else f'Unknown({self.result})'
        return f'<LoggedMatch {self.id} by User {self.logger_user_id} with Deck {self.deck_id} - {result_str} on {self.timestamp}>'