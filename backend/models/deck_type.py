from backend import db

class DeckType(db.Model):
    __tablename__ = "deck_types"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_type = db.Column(db.String(100), unique=True, nullable=False)
