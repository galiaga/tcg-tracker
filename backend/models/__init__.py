# backend/models/__init__.py

from backend.database import db
from .user import User
from .deck import Deck
from .match import Match
from .user_deck import UserDeck
from .commanders import Commander
from .commander_deck import CommanderDeck
from .deck_type import DeckType
from .tag import Tag
from .tournament import Tournament, TournamentParticipant

__all__ = [
    'User',
    'Deck',
    'DeckType',
    'Commander',
    'CommanderDeck',
    'Tag',
    'UserDeck',
    'Match',
    'Tournament',
    'TournamentParticipant',
]