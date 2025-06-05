from backend.database import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class OpponentCommanderInMatch(db.Model):
    __tablename__ = "opponent_commanders_in_match"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    logged_match_id = db.Column(db.Integer, db.ForeignKey('logged_matches.id', ondelete='CASCADE'), nullable=False, index=True)
    # seat_number refers to the actual table seat (1-4) where this opponent commander was.
    # It should NOT be the player's own seat_number for this entry.
    seat_number = db.Column(db.Integer, nullable=False, index=True) 
    commander_id = db.Column(db.Integer, db.ForeignKey('commanders.id'), nullable=False, index=True)
    
    # Role of this commander for the opponent at this seat (e.g., "primary", "partner", "background")
    # This helps distinguish if you have two commanders for one opponent.
    role = db.Column(db.String(50), nullable=False, default="primary", index=True) 

    # --- Relationships ---
    # Relationship back to LoggedMatch (many-to-one)
    # logged_match = relationship("LoggedMatch", back_populates="opponent_commanders") # Defined in LoggedMatch
    
    # Relationship to Commander (many-to-one)
    commander = relationship("Commander", lazy='joined') # lazy='joined' or 'select' based on preference

    # --- Constraints ---
    __table_args__ = (
        db.CheckConstraint('seat_number >= 1 AND seat_number <= 4', name='check_ocim_seat_number'),
        # Optional: Unique constraint to prevent adding the same commander in the same role for the same seat in a match
        # db.UniqueConstraint('logged_match_id', 'seat_number', 'commander_id', 'role', name='uq_opponent_commander_in_match_role'),
        # Or, if only one primary and one associate are allowed per seat:
        # db.UniqueConstraint('logged_match_id', 'seat_number', 'role', name='uq_opponent_commander_role_per_seat'), # This might be too restrictive if role isn't always unique
    )

    def __repr__(self):
        return f"<OpponentCommanderInMatch match_id={self.logged_match_id} seat={self.seat_number} cmd_id={self.commander_id} role='{self.role}'>"