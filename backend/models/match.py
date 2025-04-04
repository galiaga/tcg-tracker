from backend import db
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint
from backend.models.tag import match_tags

class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, server_default=func.current_timestamp(), nullable=False)
    result = db.Column(db.Integer, nullable=False)  # 0 = Lose, 1 = Win, 2 = Draw
    user_deck_id = db.Column(db.Integer, db.ForeignKey("user_decks.id"), nullable=False)

    user_deck = db.relationship("UserDeck", back_populates="matches")

    tags = db.relationship(
        "Tag",
        secondary=match_tags,
        back_populates="matches",
    )

    __table_args__ = (
        CheckConstraint("result IN (0, 1, 2)", name="check_match_result"),  
    )

    def __repr__(self):
        return f"<Match id={self.id} result={self.result} timestamp={self.timestamp}>"
