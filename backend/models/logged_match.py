import enum
from sqlalchemy import CheckConstraint, ForeignKey # Removed UniqueConstraint, Index unless needed elsewhere
from sqlalchemy.orm import relationship
from backend.database import db
# Removed: from backend.models.commanders import Commander (no longer direct FKs here for opponents)
# Import the new model
from backend.models.opponent_commander_in_match import OpponentCommanderInMatch


class LoggedMatchResult(enum.Enum):
    WIN = 0
    LOSS = 1
    DRAW = 2

match_tags = db.Table('match_tags',
    db.Column('match_id', db.Integer, db.ForeignKey('logged_matches.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class LoggedMatch(db.Model):
    __tablename__ = 'logged_matches'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    result = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    logger_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False, index=True)
    player_position = db.Column(db.Integer, nullable=False, index=True) 
    player_mulligans = db.Column(db.Integer, nullable=True)
    
    # REMOVED: commander_at_seat1_id, commander_at_seat2_id, etc.
    
    pod_notes = db.Column(db.Text, nullable=True)

    logger = relationship("User", backref=db.backref("logged_matches", lazy="dynamic"))
    deck = relationship("Deck", backref=db.backref("logged_matches", lazy="dynamic"))
    tags = relationship("Tag", secondary=match_tags, back_populates="logged_matches")

    # NEW: Relationship to OpponentCommanderInMatch (one-to-many)
    # This allows you to access all opponent commanders for a given match.
    opponent_commanders = relationship(
        "OpponentCommanderInMatch", 
        backref=db.backref("logged_match", lazy="joined"), # Or lazy="select"
        cascade="all, delete-orphan" # If a match is deleted, its opponent commander entries are also deleted
    )

    # REMOVED: commander_at_seatX_rel relationships

    __table_args__ = (
        CheckConstraint('result IN (0, 1, 2)', name='check_logged_match_result'),
        CheckConstraint('player_position >= 1 AND player_position <= 4', name='check_player_position_commander'),
        CheckConstraint('player_mulligans IS NULL OR player_mulligans >= 0', name='check_player_mulligans_non_negative'),
    )

    def get_result_enum(self) -> LoggedMatchResult | None:
        try:
            return LoggedMatchResult(self.result)
        except ValueError:
            return None

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = db.func.now()
        # Also soft-delete associated opponent commanders if they had an is_active flag (not in this model)
        # Cascade delete-orphan handles DB-level deletion if LoggedMatch is hard deleted.
        # For soft delete, you might need to iterate self.opponent_commanders if they also have soft delete.
        db.session.add(self)

    @classmethod
    def query_active(cls):
        return cls.query.filter_by(is_active=True)

    def __repr__(self):
        result_str = self.get_result_enum().name if self.get_result_enum() else f'Unknown({self.result})'
        position_map = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
        player_turn_order_text = position_map.get(self.player_position, str(self.player_position))
        mull_info = f", Mulls: {self.player_mulligans}" if self.player_mulligans is not None else ""
        
        # For __repr__, accessing opponent_commanders might trigger a query if not eager loaded.
        # This is generally fine for debugging.
        opp_info_parts = []
        if self.opponent_commanders: # Check if the relationship is loaded / has items
            # Group by seat for a more readable repr
            opps_by_seat = {}
            for oc in self.opponent_commanders:
                if oc.seat_number not in opps_by_seat:
                    opps_by_seat[oc.seat_number] = []
                opps_by_seat[oc.seat_number].append(f"{oc.commander.name[:10]}{' ('+oc.role[:1]+')' if oc.role != 'primary' else ''}")
            
            for seat, cmds in sorted(opps_by_seat.items()):
                opp_info_parts.append(f"S{seat}: {', '.join(cmds)}")
        
        opp_info = f", Pod: [{'; '.join(opp_info_parts)}]" if opp_info_parts else ""

        return (f'<LoggedMatch {self.id} User:{self.logger_user_id} Deck:{self.deck_id} - {result_str} (Player Turn: {player_turn_order_text}){mull_info}{opp_info} @ {self.timestamp}>')