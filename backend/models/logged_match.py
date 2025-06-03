# backend/models/logged_match.py
import enum
from sqlalchemy import UniqueConstraint, Index, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import db

# --- Enums ---
class LoggedMatchResult(enum.Enum):
    WIN = 0
    LOSS = 1
    DRAW = 2

# --- Association Tables ---
match_tags = db.Table('match_tags',
    db.Column('match_id', db.Integer, db.ForeignKey('logged_matches.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

# --- Main Model Definition ---
class LoggedMatch(db.Model):
    __tablename__ = 'logged_matches'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    result = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    logger_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=True, index=True)
    opponent_description = db.Column(db.Text, nullable=True)
    # match_format field is removed as the app focuses solely on Commander

    # Player's turn position in an assumed 4-player Commander pod
    player_position = db.Column(db.Integer, nullable=True, index=True)

    # --- Relationships ---
    logger = relationship("User", backref=db.backref("logged_matches", lazy="dynamic"))
    deck = relationship("Deck", backref=db.backref("logged_matches", lazy="dynamic"))
    tags = relationship("Tag", secondary=match_tags, back_populates="logged_matches")

    # --- Table Arguments & Constraints ---
    __table_args__ = (
        CheckConstraint('result IN (0, 1, 2)', name='check_logged_match_result'),
        CheckConstraint('player_position IS NULL OR (player_position >= 1 AND player_position <= 4)', name='check_player_position_commander'),
    )

    # --- Helper Methods ---
    def get_result_enum(self) -> LoggedMatchResult | None:
        try:
            return LoggedMatchResult(self.result)
        except ValueError:
            return None

    # --- Soft Delete Functionality ---
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = db.func.now()
        db.session.add(self)

    @classmethod
    def query_active(cls):
        return cls.query.filter_by(is_active=True)

    # --- Representation ---
    def __repr__(self):
        result_str = self.get_result_enum().name if self.get_result_enum() else f'Unknown({self.result})'
        position_info = ""
        if self.player_position:
            position_map = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
            position_info = f" (Pos: {position_map.get(self.player_position, self.player_position)})"
        return f'<LoggedMatch {self.id} by User {self.logger_user_id} with Deck {self.deck_id} - {result_str}{position_info} on {self.timestamp}>'