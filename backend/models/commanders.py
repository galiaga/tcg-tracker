from backend.database import db
from sqlalchemy.sql import func
from sqlalchemy.orm import class_mapper, relationship
from backend.models.commander_deck import CommanderDeck 

class Commander(db.Model):
    __tablename__ = "commanders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scryfall_id = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    flavor_name = db.Column(db.String, nullable=True)
    mana_cost = db.Column(db.String, nullable=True)
    cmc = db.Column(db.Float, nullable=True)
    type_line = db.Column(db.String, nullable=True)
    oracle_text = db.Column(db.Text, nullable=True)
    power = db.Column(db.String, nullable=True)
    toughness = db.Column(db.String, nullable=True)
    loyalty = db.Column(db.String, nullable=True)
    colors = db.Column(db.String, nullable=True)
    color_identity = db.Column(db.String, nullable=True)
    set_code = db.Column(db.String, nullable=True)
    image_url = db.Column(db.String, nullable=True)
    art_crop = db.Column(db.String, nullable=True)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    partner = db.Column(db.Boolean, default=False, nullable=False, server_default="0")
    background = db.Column(db.Boolean, default=False, nullable=False, server_default="0")
    choose_a_background = db.Column(db.Boolean, default=False, nullable=False, server_default="0")
    friends_forever = db.Column(db.Boolean, default=False, nullable=False, server_default="0")
    doctor_companion = db.Column(db.Boolean, default=False, nullable=False, server_default="0")
    time_lord_doctor = db.Column(db.Boolean, default=False, nullable=False, server_default="0")

    commander_decks = relationship(
        "CommanderDeck", 
        foreign_keys=[CommanderDeck.commander_id], 
        back_populates="commander", 
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in class_mapper(self.__class__).mapped_table.columns}

    def __repr__(self):
        return f"<Commander {self.name}>"
