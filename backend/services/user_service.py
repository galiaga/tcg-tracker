from backend import db
from backend.models.user import User

# Fetch a user from the database by username
def get_user_by_username(username):
    return db.session.query(User).filter_by(username=username).first()