from backend import db

class UserDeck(db.Model):
    __tablename__ = "user_decks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey("decks.id"), nullable=False)

    matches = db.relationship(
        "Match",
        back_populates="user_deck",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UserDeck user_id={self.user_id} deck_id={self.deck_id}>"
