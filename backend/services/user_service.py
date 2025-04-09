from backend import db
from backend.models.user import User

def get_user_by_username(username):
    return db.session.query(User).filter_by(username=username).first()