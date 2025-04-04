from backend import db
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

deck_tags = db.Table('deck_tags',
    db.Column('deck_id', db.Integer, db.ForeignKey('decks.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

match_tags = db.Table('match_tags',
    db.Column('match_id', db.Integer, db.ForeignKey('matches.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    user = db.relationship("User", back_populates="tags")

    decks = db.relationship(
        "Deck",
        secondary=deck_tags,
        back_populates="tags"
    )

    matches = db.relationship(
        "Match",
        secondary=match_tags,
        back_populates="tags"
    )

    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_user_tag_name'),)

    def __repr__(self):
        return f"<Tag id={self.id} user_id={self.user_id} name='{self.name}'>"